from fastapi import FastAPI, HTTPException
import aiosqlite
from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import random
from datetime import datetime
from fastapi.responses import RedirectResponse
from fastapi import Form, Depends, status

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class Airline(BaseModel):
    id: Optional[int]
    name: str
    foundation_date: Optional[str] = None
    country: Optional[str] = None

    @staticmethod
    def from_row(row):
        return Airline(id=row[0], name=row[1], foundation_date=row[2], country=row[3])

    @staticmethod
    def from_row_short(row):
        return Airline(id=row[0], name=row[1])



class Airplane(BaseModel):
    id: Optional[int] = None
    call_sign: str
    model: str
    capacity: int
    year_of_manufacture: str
    airline_id: Optional[int] = None
    airline_name: str = ""

    @staticmethod
    def from_row(row):
        return Airplane(id=row[0], call_sign=row[1], model=row[2], capacity=row[3], 
                        year_of_manufacture=row[4], airline_id=row[5], airline_name=row[6])



async def create_tables():
    async with aiosqlite.connect("database.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS airlines (
                            id INTEGER PRIMARY KEY,
                            name TEXT NOT NULL,
                            foundation_date TEXT,
                            country TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS airplanes (
                            id INTEGER PRIMARY KEY,
                            call_sign TEXT NOT NULL,
                            model TEXT NOT NULL,
                            capacity INTEGER,
                            year_of_manufacture TEXT,
                            airline_id INTEGER,
                            FOREIGN KEY(airline_id) REFERENCES airlines(id))''')
        await db.commit()

@app.on_event("startup")
async def startup():
    await create_tables()
    #await insert_test_data()

async def query_table(db, query, sort):
    if sort:
        query += f" ORDER BY {sort}"
    cursor = await db.execute(query)
    return await cursor.fetchall()

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse('home.html', {"request": request})

@app.get("/airlines")
async def get_airlines(request: Request, sort: Optional[str] = None):
    async with aiosqlite.connect("database.db") as db:
        rows = await query_table(db, 'SELECT * FROM airlines', sort)
        airlines = [Airline.from_row(row) for row in rows]
        return templates.TemplateResponse("table-airlines.html", {"request": request, "airlines": airlines})


@app.get("/planes")
async def get_airlines(request: Request, sort: Optional[str] = None):
    async with aiosqlite.connect("database.db") as db:
        query = 'SELECT p.*, a.name FROM airplanes p JOIN airlines a ON p.airline_id = a.id'

        if sort != None:
            sort = 'p.'+sort

        rows = await query_table(db, query, sort)
        airlines = [Airplane.from_row(row) for row in rows]
        return templates.TemplateResponse("table-planes.html", {"request": request, "planes": airlines})


@app.get("/edit-plane")
async def edit_plane_get(request: Request, id: int = None):
    airlines = []
    plane = Airplane(id=None, call_sign="", model="", capacity=0, year_of_manufacture="", airline_id=None, airline_name="")

    async with aiosqlite.connect("database.db") as db:
        if id is not None:
            cursor = await db.execute('SELECT p.*, a.name FROM airplanes p JOIN airlines a ON p.airline_id = a.id where p.id = ?', (str(id),))
            rows = await cursor.fetchall()
            plane = Airplane.from_row(rows[0])

        cursor = await db.execute('SELECT id, name FROM airlines')
        rows = await cursor.fetchall()
        airlines = [Airline.from_row_short(row) for row in rows]

    return templates.TemplateResponse('edit-plane.html', {"request": request, "plane": plane, "airlines": airlines})


@app.post("/edit-plane")
async def update_airplane(id: int = Form(None), call_sign: str = Form(), model: str = Form(), 
                          capacity: int = Form(), year_of_manufacture: str = Form(), airline_id:int = Form(),
                          action: str=Form()):
    async with aiosqlite.connect("database.db") as db:
        if action.lower() == "delete":
            assert id is not None
            await db.execute("DELETE FROM airplanes WHERE id = ?", (str(id), ))
        elif id is not None:
            await db.execute("UPDATE airplanes SET call_sign = ?, model = ?, capacity = ?, year_of_manufacture = ?, airline_id = ? WHERE id = ?", 
                         (call_sign, model, capacity, year_of_manufacture, airline_id, id))
        else:
            await db.execute("INSERT INTO airplanes (call_sign, model, capacity, year_of_manufacture, airline_id) VALUES (?, ?, ?, ?, ?)", 
                         (call_sign, model, capacity, year_of_manufacture, airline_id))
        await db.commit()
    return RedirectResponse("/planes", status_code=status.HTTP_302_FOUND)


@app.get("/edit-airline")
async def edit_airline_get(request: Request, id: int = None):
    airline = Airline(id=None, name="", foundation_date="2001", country="US")

    async with aiosqlite.connect("database.db") as db:
        if id is not None:
            cursor = await db.execute('SELECT * FROM airlines WHERE id = ?', (str(id),))
            rows = await cursor.fetchall()
            airline = Airline.from_row(rows[0])

    return templates.TemplateResponse('edit-airline.html', {"request": request, "airline": airline})

@app.post("/edit-airline")
async def update_airline(id: int = Form(None), name:str = Form(), country:str = Form(), foundation_date:str = Form()):
    async with aiosqlite.connect("database.db") as db:
        if id is not None:
            await db.execute("UPDATE airlines SET name = ?, foundation_date = ?, country = ? WHERE id = ?", (name, foundation_date, country, id))
        else:
            await db.execute("INSERT INTO airlines (name, foundation_date, country) VALUES (?, ?, ?)", (name, foundation_date, country))
        await db.commit()
    return RedirectResponse("/airlines", status_code=status.HTTP_302_FOUND)
