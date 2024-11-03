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


class PreOrderDetails(BaseModel):
    availableFrom: str
    availableTo: str
    preOrderUnTill: str

class Variation(BaseModel):
     id: int
     name: str
     shortDisplayName: str
     price: str
     currency: str
     isDefault: bool

class PriceDetails(BaseModel):
    variations: List[Variation]

class MoreItems(BaseModel):
     id: int
     title: str
     price: str
     currency: str
     image: Optional[str]

class LocationDetails(BaseModel):
     address: str
     latitude: float
     longitude: float

class Seller(BaseModel):
        id: int
        name: str
        totalNumbersSold: str
        phone: str
        profileImage: Optional[str]
        moreItems: list[MoreItems]
        location: LocationDetails

class QuantityDetails(BaseModel):
     minimumQuantity: int
     quantityAvailable: int

class  PreOrderDetails(BaseModel):   
     availableFrom: str
     availableTo: str
     preOrderUnTill: str

class Food(BaseModel):
        id: int
        title: str
        imageUrl: str
        distance: str
        seller: Seller
        starRating: str
        isVeg: bool
        # imageDownloaded: Data?
        preOrderDetails: Optional[PreOrderDetails]
        priceDetails: PriceDetails
        quantityDetails: QuantityDetails
        services: list[str]
        isBookMarked: bool

class FoodList(BaseModel):
     foods: List[Food]
     totalItems: int
     currentPage: int

class SearchInput(BaseModel):
     searchTerm: str

class Item(BaseModel):
     id: int
     quantity: int

class Order(BaseModel):
     sellerId: int
     message: str
     items: List[Item]

class OrderStatus(BaseModel):
    statusCode: int
    date: str
    orderPlacedDate: str

class ItemOrdered(BaseModel):
     id: int
     title: str
     quantity: int
     priceDetails: PriceDetails

class TotalPriceDetails(BaseModel):
     price: str
     currency: str

class Order(BaseModel):
    id: int
    status: OrderStatus
    seller: Seller
    itemsOrdered: list[ItemOrdered]
    totalPriceDetails: PriceDetails

class OrderResult(BaseModel):
     orders: list[Order]
     totalCount: int