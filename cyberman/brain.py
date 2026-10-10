from __future__ import annotations







from dataclasses import dataclass

from typing import Callable





from cyberman.ai import ClaudeBackend, OllamaBackend



from cyberman.config import AppConfig



from cyberman.executor import ExecutionResult, Executor
from cyberman.intent import infer_command_intent
from cyberman.version import APP_VERSION
from cyberman.rules.commands import ParsedCommand, parse
@dataclass



class BrainResult:



    response: str | None = None



    log_message: str | None = None



    preview_message: str | None = None











@dataclass



class Brain:



    config: AppConfig



    executor: Executor

    status_provider: Callable[[], str] | None = None







    def __post_init__(self) -> None:



        self._claude = ClaudeBackend(self.config)



        self._ollama = OllamaBackend(self.config)







    def process(self, text: str) -> BrainResult:

        normalized = self._strip_wake_word(text)

        parsed = parse(normalized)

        if parsed is None:
            intent = infer_command_intent(normalized, self.config, self._claude, self._ollama)
            if intent is not None:
                if intent.action == "chat":
                    return self._route_ai(normalized)
                parsed = ParsedCommand(intent.action, intent.args)

        if parsed is None:
            return self._route_ai(normalized)

        return self._handle(parsed)







    def _handle(self, parsed: ParsedCommand) -> BrainResult:



        action = parsed.action



        args = parsed.args







        if action == "open_app":



            result = self.executor.open_app(args[0])



        elif action == "close_app":



            result = self.executor.close_app(args[0])



        elif action == "type_text":

            result = self.executor.type_text(args[0])


        elif action == "type_text_in_app":

            result = self.executor.type_text_into_app(args[0], args[1])


        elif action == "open_url":



            result = self.executor.open_url(args[0])



        elif action == "help":



            return BrainResult(response=self._help_text(), log_message="Displayed help.")



        elif action == "about":



            return BrainResult(response=self._about_text(), log_message="Displayed about info.")



        elif action == "volume_up":



            result = self.executor.volume_up()



        elif action == "volume_down":



            result = self.executor.volume_down()



        elif action == "volume_mute":



            result = self.executor.volume_mute()



        elif action == "brightness_up":



            result = self.executor.brightness_up()



        elif action == "brightness_down":



            result = self.executor.brightness_down()



        elif action == "battery_status":



            result = self.executor.battery_status()



        elif action == "shutdown":



            result = self.executor.shutdown()



        elif action == "restart":



            result = self.executor.restart()



        elif action == "sleep":



            result = self.executor.sleep()



        elif action == "voice_status":



            return BrainResult(response=self._voice_status_text(), log_message="Reported voice status.")



        elif action == "copy_path":



            preview = self._preview_path_action("copy", args[0], args[1])



            result = self.executor.copy_path(args[0], args[1])



            return BrainResult(



                response=result.message,



                log_message=self._format_log(result),



                preview_message=preview,



            )



        elif action == "move_path":



            preview = self._preview_path_action("move", args[0], args[1])



            result = self.executor.move_path(args[0], args[1])



            return BrainResult(



                response=result.message,



                log_message=self._format_log(result),



                preview_message=preview,



            )



        elif action == "rename_path":



            preview = self._preview_path_action("rename", args[0], args[1])



            result = self.executor.rename_path(args[0], args[1])



            return BrainResult(



                response=result.message,



                log_message=self._format_log(result),



                preview_message=preview,



            )



        elif action == "delete_path":



            preview = self._preview_path_action("delete", args[0], None)



            result = self.executor.delete_path(args[0])



            return BrainResult(



                response=result.message,



                log_message=self._format_log(result),



                preview_message=preview,



            )



        elif action == "create_file":



            preview = self._preview_path_action("create", args[0], None)



            result = self.executor.create_file(args[0], args[1])



            return BrainResult(



                response=result.message,



                log_message=self._format_log(result),



                preview_message=preview,



            )



        elif action == "read_file":



            preview = self._preview_path_action("read", args[0], None)



            result = self.executor.read_file(args[0])



            return BrainResult(



                response=result.message,



                log_message=self._format_log(result),



                preview_message=preview,



            )



        elif action == "search_files":



            result = self.executor.search_files(args[1], args[0])



        elif action == "list_files":



            result = self.executor.list_files(args[0] or ".")



        elif action == "create_folder":



            preview = self._preview_path_action("create folder", args[0], None)



            result = self.executor.create_folder(args[0])



            return BrainResult(



                response=result.message,



                log_message=self._format_log(result),



                preview_message=preview,



            )



        else:



            return BrainResult(response="I do not know how to handle that yet.")







        return BrainResult(response=result.message, log_message=self._format_log(result))







    def _fallback(self, text: str) -> BrainResult:



        return BrainResult(



            response=f"I heard: {text}. I can handle commands, but that one needs the AI layer or a new rule.",



            log_message="No rule-based match.",



        )







    def _help_text(self) -> str:



        return (



            "You can say things like: open chrome, open https://example.com, "



            "copy file.txt to Downloads, move file.txt to Documents, rename old.txt to new.txt, "



            "delete file.txt, create file notes.txt with hello, read file notes.txt aloud, "



            "search report in Downloads, list files in Downloads, make folder Projects, volume up, volume down, mute, "



            "open file manager, open chrome, close notepad, close the notepad, type hello world in notepad, type hello world into word, brightness up, brightness down, battery status, shutdown, restart, or sleep."



        )







    def _about_text(self) -> str:



        return (



            f"{self.config.assistant_name} v{APP_VERSION} is a Windows assistant with voice input, a dashboard, "



            "online/offline AI routing, safe command execution, and packaged Windows release support."



        )







    @staticmethod



    def _preview_path_action(action: str, source: str, destination: str | None) -> str:



        if destination:



            return f"Preview: {action} '{source}' -> '{destination}'"



        return f"Preview: {action} '{source}'"







    def _route_ai(self, text: str) -> BrainResult:



        mode = self.config.ai_mode.lower().strip()



        providers: list[tuple[str, object]] = []







        if mode in {"auto", "online", "online only"}:



            providers.append(("claude", self._claude))



        if mode in {"auto", "offline", "offline only"}:



            providers.append(("ollama", self._ollama))







        for provider_name, provider in providers:



            if not getattr(provider, "ready", False):



                continue



            response = provider.chat(text)  # type: ignore[call-arg]



            if response.ok:



                return BrainResult(



                    response=response.response,



                    log_message=f"[{provider_name.upper()}] {response.response}",



                )







        return self._fallback(text)







    def _strip_wake_word(self, text: str) -> str:



        wake_word = self.config.wake_word.strip().lower()



        cleaned = text.strip()



        lowered = cleaned.lower()



        if lowered.startswith(wake_word):



            remainder = cleaned[len(wake_word) :].lstrip(" ,.:;!-")



            return remainder or cleaned



        return cleaned







    @staticmethod



    def _format_log(result: ExecutionResult) -> str:



        status = "OK" if result.ok else "ERR"



        return f"[{status}] {result.message}"




