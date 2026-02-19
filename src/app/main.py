import FastAPI
import langgraph

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/plan")
async def plan():
    return {"plan": "This is your travel plan."}