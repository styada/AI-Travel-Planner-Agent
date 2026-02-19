.PHONY start

start:
	echo "Starting the AI Travel Planner Agent..."
	poetry run uvicorn src.app.main:app --reload