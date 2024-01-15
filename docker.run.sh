#!/bin/bash
exec uvicorn main:app --host $HOST --port $PORT