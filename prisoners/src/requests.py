from pathlib import Path

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from tortoise.contrib.fastapi import HTTPNotFoundError

from prisoners.src.models import PrisonerRequest, Prisoner
from prisoners.src.schemas import Request_Pydantic
from prisoners.dependencies import send_email_async


requests_views = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@requests_views.get('/',
                     response_class=HTMLResponse,
                     response_model=Request_Pydantic,
                     responses={404: {"model": HTTPNotFoundError}})
async def get_all_requests(request: Request):
    requests_data = await Request_Pydantic.from_queryset(PrisonerRequest.all())
    prisoners_count = await Prisoner.all().count()
    return templates.TemplateResponse('requests.html', {"request": request, 
                                                        "requests_data": requests_data,
                                                        'prisoners_count': prisoners_count}) 


@requests_views.get('/{request_id}', 
                     response_class=HTMLResponse,
                     response_model=Request_Pydantic,
                     responses={404: {"model": HTTPNotFoundError}})
async def get_request_by_id(request: Request, 
                            request_id: int):
    request_data = await Request_Pydantic.from_queryset_single(PrisonerRequest.get(id=request_id))
    request_data.created_at = (str(request_data.created_at)).split('.')[0]
    return templates.TemplateResponse('request.html', {"request": request,
                                                       "request_data": request_data})


@requests_views.delete('/decline/{request_id}')
async def delete_request_by_id(request_id: int):
    request_data = await Request_Pydantic.from_queryset_single(PrisonerRequest.get(id=request_id))
    await send_email_async('Запрос отклонён', 
                     'email_decline.html',
                     request_data)
    
    deleted = await PrisonerRequest.filter(id=request_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    return {'email_sent': True,
            'request_deleted': True, 
            'request_id': request_id}
    

@requests_views.delete('/confirm/{request_id}')
async def delete_request_by_id(request_id: int):
    request_data = await Request_Pydantic.from_queryset_single(PrisonerRequest.get(id=request_id))
    await send_email_async('Запрос подтверждён', 
                           'email_confirm.html',
                           request_data)
    
    deleted = await PrisonerRequest.filter(id=request_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    return {'email_sent': True,
            'request_deleted': True, 
            'request_id': request_id}


