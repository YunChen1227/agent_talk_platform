import argparse
import uvicorn
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AgentMatch Platform Backend")
    parser.add_argument("--mode", type=str, default="prod", choices=["dev_1", "dev_2", "prod"], help="Run mode: dev_1 (JSON ES) | dev_2 (local ES) | prod")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    # Set environment variable before importing app
    os.environ["MODE"] = args.mode
    
    log_level = "debug" if args.mode.startswith("dev") else "info"
    
    print(f"Starting server in {args.mode.upper()} mode with log level {log_level.upper()}...")
    
    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload, log_level=log_level)
