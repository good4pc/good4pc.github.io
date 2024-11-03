from contextvars import Token
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, status
import jwt
from pydantic import BaseModel
from typing import Optional
from typing import List
import psycopg2
from psycopg2.extras import  RealDictCursor
import time
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException
from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from enum import Enum
from Orders import Seller, Food, FoodList, Order,SearchInput, PreOrderDetails,PriceDetails,QuantityDetails,LocationDetails, MoreItems,Variation, OrderStatus,ItemOrdered,OrderResult, TotalPriceDetails


app = FastAPI()
# https://www.youtube.com/watch?v=0sOvCWFmrtA&list=PL1PAHFHK_SNHJPwDwHN5SptU5I_OvU_Oz
class LoginUserModel(BaseModel):
     userName: str
     password: str

class User(BaseModel):
     name: str
     phone: str
     is_seller: bool
     email: str
     password: str
     countryCode: str

class ErrorCodes(Enum):
     INCORRECT_PASSWORD = 1001
     PASSWORD_EMPTY = 1002
     USER_NAME_EMPTY = 1003
     USER_NOT_SIGNED_UP = 1004
     USER_NOT_FOUND = 1005

# Authentication Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://127.0.0.1:8000/token")


# Password encryptor
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Access Token

ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 4
# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "c535920f0fe3064dd7cd09ed630761823d4f34fede9cc969eea8a2512cc1ea2e"
ALGORITHM = "HS256"

signedUpusers: List[User] = list()
loggedInUsers: List[User] = list()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

while True:
     try:
          conn = psycopg2.connect(host='localhost', database = 'Umami', user='postgres',password='8899', cursor_factory=RealDictCursor)
          cursor = conn.cursor()
          print("Database connection was successfull!!")
          break
     except Exception as error:
          print("Connecting to database failed")
          print("Error: ", error)
          time.sleep(2)

user: Optional[User] = None


@app.get("/")
def read_root():
    return { "Hello": "Hello workd"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": f"{item_id}"}



def verify_password(plainPassword, hashed_password):
     return pwd_context.verify(plainPassword, hashed_password)

def get_password_hash(password):
     return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/login")
async def login_for_Access_token(loginUserModel: LoginUserModel):
     if len(loginUserModel.userName) == 0:
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail=ErrorCodes.USER_NAME_EMPTY.value)

     if len(loginUserModel.password) == 0:
         raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= ErrorCodes.PASSWORD_EMPTY.value) 

     for user in signedUpusers:
          currentUserEmail = user.email.lower()
          loginUserEmail = loginUserModel.userName.lower()
          if currentUserEmail == loginUserEmail:
               if verify_password(loginUserModel.password, user.password):
                    # Hard coded id, which needs to be changed
                    # Return new authorization token
                    loggedInUsers.append(user)
                    token = createAccessToken(email=user.email)
                    return { "id": 10554, "name": user.name, "phone": user.phone, "email": user.email, "token": token.access_token }
               else:
                    raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail= ErrorCodes.INCORRECT_PASSWORD.value)
                    
     raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail=ErrorCodes.USER_NOT_SIGNED_UP.value)

def createAccessToken(email: str):
       access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
       access_token = create_access_token(data={"sub": email}, expires_delta=access_token_expires)
       token = Token(access_token=access_token, token_type="bearer")
       return token

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        print(username)
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=username)
    if user is None:
        raise credentials_exception
    return user

def get_user(username: str):
     for user in signedUpusers:
          currentUserEmail = user.email.lower()
          usernameLowered = username.lower()
          if currentUserEmail == username:
               return user

@app.post("/signup")
def signUp(user: User):
     # cursor.execute(""" INSERT INTO public."Users"
     #                 (name, phone, is_seller, address, pin_code, email,password, country ) 
     #                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s) WHERE NOT EXIST (SELECT email FROM public."Users" users_table WHERE users_table.email = %s)
     #                 RETURNING *""", 
     #                 (user.name, user.phone, user.is_seller, user.address, user.pin_code, user.email, user.password, user.country, user.email))
     # users = cursor.fetchone()
     # conn.commit()
     if signedUpusers.__contains__(user):
          return {"data": "user already exists"}
     else:
          newUpdatedUser = user
          newUpdatedUser.password = get_password_hash(user.password)
          token = createAccessToken(email=user.email)
          signedUpusers.append(newUpdatedUser)
     return { "id": 10554, "name": user.name, "phone": user.phone, "email": user.email, "token": token.access_token }

@app.post("/sign_out")
async def signOut(currentUser: Annotated[User, Depends(get_current_user)]):
     if currentUser is not None:
          for user in loggedInUsers:
               if user == currentUser:
                    loggedInUsers.remove(user)
                    return { "data": "successfully signed out"}
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCodes.USER_NOT_FOUND.value)

        
@app.post("/complete_order")
async def completeOrder(currentUser: Annotated[User, Depends(get_current_user)], order: Order):
   print(order)
   return {"data": "completed"}



@app.post("/foods_listing")
async def foodListing(searchTerm: SearchInput):
   image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYiV3KUdtKlifN1R9ZDm1YTb6P0ZR7tm010A&s"
   yogaImage = "data:image/jpeg;base64,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"
   moreItems = [MoreItems(id=12, title="hike", price="250", currency="CAD", image="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYiV3KUdtKlifN1R9ZDm1YTb6P0ZR7tm010A&s"), MoreItems(id=14, title="Deep see fishign", price="120", currency="CAD", image="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYiV3KUdtKlifN1R9ZDm1YTb6P0ZR7tm010A&s")]
   seller = Seller(id=1245,name="PC",totalNumbersSold="100", phone="423434234",address="as", profileImage="",moreItems=moreItems,location=LocationDetails(address="",latitude=234234.324, longitude=4398439.233))
   food1 = Food(id=1,title="Fishing charter",imageUrl=image,distance="100m away", seller=seller,starRating="5",isVeg=False,preOrderDetails= None,priceDetails=PriceDetails(variations=[Variation(id=1221,name="Medium", shortDisplayName="M",price="120",currency="CAD", isDefault=True)]),quantityDetails=QuantityDetails(minimumQuantity=1,quantityAvailable=10),services=[], isBookMarked=False)
   variations = [Variation(id=1221,name="Weekly", shortDisplayName="W",price="120",currency="CAD", isDefault=True), Variation(id=1221,name="Monthly", shortDisplayName="W",price="120",currency="CAD", isDefault=True)]
   priceDetails = PriceDetails(variations=variations)
   food2 = Food(id=2,title="Yoga classes(Daily)",imageUrl=yogaImage,distance="2km away", seller=seller,starRating="5",isVeg=False,preOrderDetails= None,priceDetails=priceDetails,quantityDetails=QuantityDetails(minimumQuantity=1,quantityAvailable=10),services=[], isBookMarked=False)
   food3 = Food(id=4,title="Yoga classes(Daily)",imageUrl=yogaImage,distance="2km away", seller=seller,starRating="5",isVeg=False,preOrderDetails= None,priceDetails=priceDetails,quantityDetails=QuantityDetails(minimumQuantity=1,quantityAvailable=10),services=[], isBookMarked=False)
   food4 = Food(id=12,title="Yoga classes(Daily)",imageUrl=yogaImage,distance="2km away", seller=seller,starRating="5",isVeg=False,preOrderDetails= None,priceDetails=priceDetails,quantityDetails=QuantityDetails(minimumQuantity=1,quantityAvailable=10),services=[], isBookMarked=False)
   food5 = Food(id=23,title="Yoga classes(Daily)",imageUrl=yogaImage,distance="2km away", seller=seller,starRating="5",isVeg=False,preOrderDetails= None,priceDetails=priceDetails,quantityDetails=QuantityDetails(minimumQuantity=1,quantityAvailable=10),services=[], isBookMarked=False)

   foods = [food1, food2, food3, food4, food5]
   foods_search = [food1]
   foodList = FoodList(foods=foods, totalItems=1, currentPage=1)

   if not searchTerm.searchTerm:
         return FoodList(foods=foods, totalItems=1, currentPage=1)
   else:
        return FoodList(foods=foods_search, totalItems=1, currentPage=1)

class  Availability(BaseModel):
     isAvailable: bool
     status: int

class Subscription(BaseModel):
      variations: list[Variation]

class DatesPickerConfigurator(BaseModel):
     predefinedDates: Optional[list[str]]
     disabledDates: Optional[list[str]]

class FoodDetailsModel(BaseModel):
    id: int
    title: str
    isVeg: bool
    availability: Availability
    description: str
    preOrderDetails: Optional[PreOrderDetails]
    location: LocationDetails
    distance: str
    seller: Seller
    images: list[str]
    subscription: Optional[Subscription]
    priceDetails: PriceDetails
    quantityDetails: QuantityDetails
    youMayAlsoLike: list[MoreItems]
    datesPickerConfigurator: DatesPickerConfigurator
    availableOnlyOn: Optional[str]
    payByCashEnabled: bool



@app.post("/food_details/{id}")
async def foodDetails(id: int):
       moreItems = [MoreItems(id=12, title="hike", price="1200", currency="CAD", image="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYiV3KUdtKlifN1R9ZDm1YTb6P0ZR7tm010A&s"), MoreItems(id=14, title="Running Every day", price="120", currency="CAD", image="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYiV3KUdtKlifN1R9ZDm1YTb6P0ZR7tm010A&s")]

       datesConfigurator = DatesPickerConfigurator(predefinedDates=None,disabledDates=["Oct 19,2024"])
       images = ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYiV3KUdtKlifN1R9ZDm1YTb6P0ZR7tm010A&s", "data:image/jpeg;base64,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","data:image/jpeg;base64,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" ]
       availability = Availability(isAvailable=True, status=1)
       variations = [Variation(id=10,name="11.00AM", shortDisplayName="M",price="35.0",currency="CAD", isDefault=True), Variation(id=12,name="12.00AM", shortDisplayName="L",price="55.0",currency="CAD", isDefault=True)]
       priceDetails = PriceDetails(variations=variations)
       seller = Seller(id=1245,name="PC",totalNumbersSold="100", phone="423434234", profileImage="https://static.wikia.nocookie.net/bollywood/images/0/04/Shah_Rukh_Khan.jpg/revision/latest?cb=20220122154417",moreItems=moreItems,location=LocationDetails(address="Tap and find",latitude=43.712664, longitude=-79.395977))
       if id == 1:
            return FoodDetailsModel(id=id,title="All Day fishing charter",isVeg=False,availability=availability,description="Whether it’s a family outing, a unique corporate event, client customer appreciation or a celebration of a special day, our mission is to exceed your expectations with our friendly, knowledgeable and professional crew. We offer sport fishing for world class salmon and trout as well as pleasure cruising to the Toronto Islands for a BBQ. We can accommodate any size group, as we can provide additional boats upon request. Come escape the city and relax in style.",preOrderDetails=None, location=LocationDetails(address="Erskine",latitude=43.712664, longitude=-79.395977),distance="233", seller=seller,images=images,subscription=None,priceDetails=priceDetails,quantityDetails=QuantityDetails(minimumQuantity=1, quantityAvailable=10),youMayAlsoLike=moreItems, datesPickerConfigurator=datesConfigurator, availableOnlyOn= None, payByCashEnabled= True)
       else:
          variations = [Variation(id=10,name="Weekly", shortDisplayName="W",price="120",currency="CAD", isDefault=True), Variation(id=12,name="Monthly", shortDisplayName="W",price="100",currency="CAD", isDefault=True)]
          subscriptions = Subscription(variations=variations)
          return FoodDetailsModel(id=id,title="Bread Omlet",isVeg=False,availability=availability,description="it is lur ",preOrderDetails=None, location=LocationDetails(address="88 Erskine Ave, Toronto, Canada",latitude=89787.09,longitude=8748723.234),distance="233", seller=seller,images=images,subscription=subscriptions,priceDetails=priceDetails,quantityDetails=QuantityDetails(minimumQuantity=1, quantityAvailable=10),youMayAlsoLike=moreItems, datesPickerConfigurator=datesConfigurator, availableOnlyOn= None, payByCashEnabled=False)

@app.get("/seller_reviews/{id}")
async def sellerReview(id: int):
     return {
          "reviews": [{
               "id": 123,
               "name": "PRasanth pc",
               "date": "",
               "ratingCount": 3,
               "ratingMaxCount": 5,
               "description": "best fishing experiemce i ever had"
          },
          {
               "id": 144,
               "name": "Achu",
               "date": "",
               "ratingCount": 3,
               "ratingMaxCount": 5,
               "description": "you must go with this team"
          }],
          "totalReview": 2
     }

@app.post("/orders")
async def loadOrders(searchTerm: SearchInput):
     moreItems = [MoreItems(id=12, title="hike", price="1200", currency="CAD", image="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYiV3KUdtKlifN1R9ZDm1YTb6P0ZR7tm010A&s"), MoreItems(id=14, title="Running Every day", price="120", currency="CAD", image="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYiV3KUdtKlifN1R9ZDm1YTb6P0ZR7tm010A&s")]

     variations = [Variation(id=1221,name="Weekly", shortDisplayName="W",price="120",currency="CAD", isDefault=True), Variation(id=1221,name="Monthly", shortDisplayName="W",price="120",currency="CAD", isDefault=True)]
     priceDetails = PriceDetails(variations=variations)
     seller = Seller(id=1245,name="PC",totalNumbersSold="100", phone="423434234", profileImage="https://static.wikia.nocookie.net/bollywood/images/0/04/Shah_Rukh_Khan.jpg/revision/latest?cb=20220122154417",moreItems=moreItems,location=LocationDetails(address="Tap and find",latitude=43.712664, longitude=-79.395977))

     orderStatus = OrderStatus(statusCode=1,date="",orderPlacedDate="")
     order1 = Order(id=1, status=orderStatus,seller=seller,itemsOrdered=[ItemOrdered(id=2,title="",quantity=2,priceDetails=priceDetails)], totalPriceDetails=priceDetails) 
     order2 = Order(id=2, status=orderStatus,seller=seller,itemsOrdered=[ItemOrdered(id=2,title="",quantity=2,priceDetails=priceDetails)], totalPriceDetails=priceDetails) 

     if not searchTerm.searchTerm:
            return OrderResult(orders=[order1], totalCount=1)
     else:
          return OrderResult(orders=[order1, order2], totalCount=2)

@app.get("/load_filters")
async def load_filters():
     return {
          "filterGroups":[
               {
                   "id": 10,
                   "name": "Distance",
                   "filters": [{"id": 1, "name": "less than 1km"},
                               {"id": 2, "name": "less than 2km"}]

               },
               {
                   "id": 11,
                   "name": "star rating",
                   "filters": [{"id": 1, "name": "5 star rating"},
                               {"id": 2, "name": "6 start rating"}]
               },
                {
                   "id": 12,
                   "name": "Activity",
                   "filters": [{"id": 1, "name": "Dogwalking"},
                               {"id": 2, "name": "Hiking"}]
               },
               {
                   "id": 13,
                   "name": "Activity",
                   "filters": [{"id": 1, "name": "Dogwalking"},
                               {"id": 2, "name": "Hiking"}]
               },
                {
                   "id": 14,
                   "name": "Activity",
                   "filters": [{"id": 1, "name": "Dogwalking"},
                               {"id": 2, "name": "Hiking"}]
               },
                {
                   "id": 15,
                   "name": "Activity",
                   "filters": [{"id": 1, "name": "Dogwalking"},
                               {"id": 2, "name": "Hiking"}]
               },
                {
                   "id": 16,
                   "name": "Activity",
                   "filters": [{"id": 1, "name": "Dogwalking"},
                               {"id": 2, "name": "Hiking"}]
               }
          ]
     }