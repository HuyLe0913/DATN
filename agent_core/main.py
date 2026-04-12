import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import litellm
from colorama import init, Fore, Style
from agent.orchestrator import Agent
from schemas.agent import AgentRequest

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

init(autoreset=True)

litellm.suppress_debug_info = True
litellm.set_verbose = False

async def main():
    print(f"DEBUG: Using model {os.getenv('AGENT_MODEL_NAME')} with tools...")
    agent = Agent(workspace_base="./agent_workspace")
    
    print("Đang tải cấu hình MCP từ mcp.json...")
    success = await agent.load_mcp_config("mcp.json")
    if success:
        print("Tích hợp công cụ MCP thành công.")
    else:
        print("Cảnh báo: Cấu hình MCP thất bại hoặc không có server nào được kết nối. Chạy với các công cụ tích hợp sẵn.")

    print(f"\n{Fore.YELLOW}Agent đã sẵn sàng. Gõ 'exit' để thoát, 'reset' để xóa lịch sử.")
    
    try:
        while True:
            try:
                user_input = input(f"\n{Fore.CYAN}Người dùng: {Style.RESET_ALL}")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                if user_input.lower() == "reset":
                    agent.messages = []
                    print(f"{Fore.MAGENTA}Đã xóa lịch sử trò chuyện.")
                    continue
                    
                request = AgentRequest(user_request=user_input)
                response = await agent.process_request(request)
                
                print(f"\n{Fore.GREEN}Trợ lý: {Style.RESET_ALL}{response.result}")
                print(f"{Style.DIM}(Đã xử lý trong {response.processing_time:.2f}s)")
            except KeyboardInterrupt:
                break
            except Exception as e:
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
