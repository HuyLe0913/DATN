import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import litellm
from colorama import init, Fore, Style
from agent.orchestrator import Agent
from schemas.agent import AgentRequest

import logging
from datetime import datetime

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"session_{timestamp}.log"

# Handler cho file (lưu toàn bộ)
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Handler cho console (hiển thị tóm tắt)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(message)s'))

# Cấu hình LOGGERS
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

full_logger = logging.getLogger("full_audit")
full_logger.setLevel(logging.INFO)
full_logger.addHandler(file_handler)
full_logger.propagate = False

logger = logging.getLogger("agent_main")

init(autoreset=True)

litellm.suppress_debug_info = True
litellm.set_verbose = False

async def main():
    logger.info(f"DEBUG: Using model {os.getenv('AGENT_MODEL_NAME')} with tools...")
    agent = Agent(workspace_base="./agent_workspace")
    
    logger.info("Đang tải cấu hình MCP từ mcp.json...")
    success = await agent.load_mcp_config("mcp.json")
    if success:
        logger.info("Tích hợp công cụ MCP thành công.")
    else:
        logger.info("Cảnh báo: Cấu hình MCP thất bại hoặc không có server nào được kết nối. Chạy với các công cụ tích hợp sẵn.")

    print(f"\n{Fore.YELLOW}Agent đã sẵn sàng. Gõ 'exit' để thoát, 'reset' để xóa lịch sử.")
    
    try:
        while True:
            try:
                user_input = input(f"\n{Fore.CYAN}Người dùng: {Style.RESET_ALL}")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                if user_input.lower() == "reset":
                    agent.messages = []
                    logger.info("Đã xóa lịch sử trò chuyện.")
                    continue
                    
                request = AgentRequest(user_request=user_input)
                response = await agent.process_request(request)
                
                print(f"\n{Fore.GREEN}Trợ lý: {Style.RESET_ALL}{response.result}")
                logger.info(f"Trợ lý: {response.result}")
                logger.info(f"(Đã xử lý trong {response.processing_time:.2f}s)")
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.exception(f"Lỗi nghiêm trọng trong quá trình xử lý: {e}")
                print(f"{Fore.RED}Lỗi: {e}")
    finally:
        print(f"\n{Fore.YELLOW}Đang đóng các kết nối...")
        try:
            await agent.mcp_integrator.close_all()
            await asyncio.sleep(0.5)
        except Exception:
            pass
        print(f"{Fore.GREEN}Đã thoát an toàn.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError):
        pass
