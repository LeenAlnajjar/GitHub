from fastapi import FastAPI, Query,Path, HTTPException, status,Body , Request
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import  HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from starlette.status import HTTP_400_BAD_REQUEST
from database import cars
from fastapi.responses import RedirectResponse

templete = Jinja2Templates(directory= 'templets')

'''
With Jinja, you can build rich templates that power the front end of your Python web applications.
It allows you to process a block of text, insert values from a context dictionary, control how the text flows using conditionals and loops,
modify inserted data with filters, and compose different templates together using inheritance and inclusion.
'''

class Car(BaseModel):
    make: Optional[str]
    model: Optional[str]
    year: Optional[int] = Field((...), ge = 1950 , le= 2022) # Field is optional but if exist it should be greater than 1950 and less than 2022 (it adds restrictions to the required field)
    price: Optional[float]
    engine: Optional[str] = "V4"
    autonomous: Optional[bool]
    sold: Optional[List[str]]

"""
BaseModel is a core component of Pydantic, used for defining and validating data models.
It plays a crucial role in FastAPI's data handling, ensuring type safety and validation.
NOTE: the dots in the pydantic field means that there is no default value required.
"""

app = FastAPI()
app.mount('/static',StaticFiles(directory = 'statics'), name = 'statics' )

'''
In FastAPI, you can serve static files (such as CSS, JavaScript, images, etc.) using the StaticFiles class.
The app.mount() method allows you to “mount” a sub-application that handles static files under a specific URL path.

'''
@app.get("/", response_class=RedirectResponse)  # As you specify the type of response model , you can specify type of response class to enscabsulate our templete response
def root(request:Request):
    '''
    First thing is to include our request from html page as an parameter from our root , this will be done using request class
    '''
    return RedirectResponse(url= '/cars')   # Tou need to add some arguments to specify things this should be done via things like home.html , you need to pass the request each time html is called

"""
what the get root actually do is to split the items in the database into integer and list and then allow the user to just pick specific
number of records from the databse. Use the query to specify the numbers of allowed record return with each request.

"""

#Redirect respone is used to redirect the response from the home page (root) to the required page

@app.get("/cars", response_class = HTMLResponse)
def get_cars(request: Request,number: Optional[int] = Query(10, le=10)):
    response = []
    for id, car in list(cars.items())[:int(number)]:
        to_add = {str(id): car}
        response.append(to_add)
    return templete.TemplateResponse("home.html",{"request":request,"cars":response,"title":"Home"})


@app.get('/cars/{id}',  response_class= HTMLResponse)
def get_car_by_id (request: Request,number,id: int = Path(...,ge=0 , le = 1000)):
    car = cars.get(id)
    if not car:
        raise HTTPException (status_code= status.HTTP_404_NOT_FOUND, detail= "Not found car by ID")
    return templete.TemplateResponse("home.html",{"request":request})

@app.post('/cars',status_code= status.HTTP_201_CREATED)
def add_cars(body_cars:List[Car],min_id: Optional[int]= Body(0)): # To add the cars to the body
    if len(body_cars)<1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,details = "No cars to add")
    min_id = len(cars.values())+ min_id
    for car in body_cars:
        while cars.get(min_id):
            min_id +=1
        cars[min_id] = car
        min_id +=1    

@app.put('/cars/{id}', response_model=Dict[str,Car]) # You should enter all values
def update_car(id: int, car: Car = Body(...)):
    stored = cars.get(id)
    if not stored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ID is not found, please check and try again!")

    stored = Car(**stored)
    new = car.dict(exclude_unset=True)
    updated_car = stored.copy(update=new)
    cars[id] = jsonable_encoder(updated_car)
    return updated_car

'''
You retrieve the existing car data from the database using cars.get(id).
Then, you create a new Car instance from the stored data: stored = Car(**stored).
Next, you extract the updated fields from the request body using car.dict(exclude_unset=True).
Finally, you update the stored car with the new data: new = stored.copy(update=new)

'''

@app.delete('/cars/{id}')
def delete_Car(id:int):
    if not cars.get(id): #Get the car ID that you want to delete it
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ID is not found, please check and try again!")
    del cars[id] #The keyword you use to delete an item from database
    