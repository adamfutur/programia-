# Flask: User JWT Authentication

Implement a login app to handle user authentication, allowing users to log in and obtain access and refresh tokens. Additionally, create a `list_users` that is accessible only to authorized and authenticated users.  

## Environment

- Python version: 3.11
- Flask version: 3.0.3
- Flask-SQLAlchemy: 3.1.1
- Default Port: 8000

## Read-Only Files

- tests/\*

## Commands

- install:

```bash
virtualenv venv && source venv/bin/activate && pip install -r requirements.txt
```

- run:

```bash
flask init-db && flask run -p 8000
```

- test:

```bash
python -m pytest --junitxml=unit.xml
```

## API Endpoint Descriptions

The login app should adhere to the following API format and response codes:

`POST /token/`
- Authenticates users and issues access and refresh tokens.  
- Expects a JSON object in the request body with _username_ and _password_ as fields. You can assume the provided data is always in the correct format.  
- If the provided credentials are valid, the response code is 200, and the response body contains the issued access and refresh tokens. 
- If the credentials are invalid, the response code is 401, and the response body includes an error message: `"detail": "Invalid username or password"`.

`GET /list/`
- Returns a collection of all user records.  
- Requires a valid Authorization token in the request header (e.g., `Bearer <token>`).  
- If a valid token is provided, The response code is 200, and the response body is an array of user records.  
- If the Authorization token is missing, the response code is 401, and the response body includes the following error message: `"msg": "Missing Authorization Header"`.
- If the provided token is invalid or expired, the response code is 401, and the response body includes the following error message: `"detail": "Invalid username or password."`.

## Sample Requests & Responses
<details><summary>Expand to view details on sample requests and responses for each endpoint.</summary>  

`POST /token/`

Request:
```
{
  "username": "example",
  "password": "password123"
}
```  

Response:  
```
Response code: 200
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
}
```  

`POST /token/`

Request:
```
{
  "username": "example",
  "password": "wrongpassword"
}
```

Response:
```
Response code: 401
{
  "detail": "Invalid username or password"
}
```

`GET /list/`

Response: 
```
Response code: 401
{
  "msg": "Missing Authorization Header"
}
```
</details>
