import argparse
import uvicorn
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AgentMatch Platform Backend")
    parser.add_argument("--mode", type=str, default="prod", choices=["dev", "prod"], help="Run mode: dev (local DB) or prod (cloud DB)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    # Set environment variable before importing app
    os.environ["MODE"] = args.mode
    
    # Set log level based on mode
    log_level = "debug" if args.mode == "dev" else "info"
    
    print(f"Starting server in {args.mode.upper()} mode with log level {log_level.upper()}...")
    
    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload, log_level=log_level)
