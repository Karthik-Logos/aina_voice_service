import logging
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, ChatContext
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import  silero
from livekit.plugins import noise_cancellation
from livekit.agents import ChatContext
from prompt_s import agent_prompt
from prompts import get_engagement_prompt , get_counselling_prompt , get_insights_prompt , get_router_prompt
from livekit.plugins import (
    google,
    noise_cancellation,
)


logger = logging.getLogger("Aina-Voice Agent")
logger.setLevel(logging.INFO)

load_dotenv()

@dataclass
class UserData:
    """Stores data to be shared across the session"""
    student_name: Optional[str] = None
    students_choice_of_exam: Optional[str] = None
    conversation_context: Optional[str] = None

    def summarize(self) -> str:
        base = "User data: Aina-Voice Agent"
        if self.student_name:
            base += f". Student: {self.student_name}"
        if self.students_choice_of_exam:
            base += f". Exam: {self.students_choice_of_exam}"
        if self.conversation_context:
            base += f". Context: {self.conversation_context}"
        return base

RunContext_T = RunContext[UserData]

class Router(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        prompt = agent_prompt('router')
        if chat_ctx is None:
            chat_ctx = ChatContext()
        super().__init__(instructions=prompt, chat_ctx=chat_ctx)

    async def on_enter(self) -> None:
        logger.info("Entering Router")
        await self.session.generate_reply(
            instructions=f"Greet the user and introduce yourself briefly as the routing agent."
        )

    @function_tool
    async def transfer_to_engagement(self) -> Agent:
        """Use this tool when the user wants to engage or they don't know what they need to do next."""
        return Engagement(chat_ctx=self.chat_ctx)
    
    @function_tool
    async def transfer_to_quiz(self) -> Agent:
        """Use this tool when the user wants to take a quiz."""
        return Quiz(chat_ctx=self.chat_ctx)

    @function_tool
    async def transfer_to_insights(self) -> Agent:
        """Use this tool when the user wants to get insights about their Quiz performance."""
        return InsightsAgent(chat_ctx=self.chat_ctx)

    @function_tool
    async def transfer_to_counselling(self) -> Agent:
        """Use this tool when the user wants to book a counselling session."""
        return CounsellingAgent(chat_ctx=self.chat_ctx)

    @function_tool
    async def transfer_to_couse_enollment(self) -> Agent:
        """Use this tool when the user wants to enroll in Bridge course."""
        return CourseAgent(chat_ctx=self.chat_ctx)
    
class Engagement(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        prompt = agent_prompt('engagement')
        if chat_ctx is None:
            chat_ctx = ChatContext()
        super().__init__(instructions=prompt, chat_ctx=chat_ctx)

    async def on_enter(self) -> None:
        logger.info("Entering Engagement")
        await self.session.generate_reply(
            instructions=f"Greet the user and introduce yourself briefly as the engagement agent."
        )

    @function_tool
    async def transfer_to_router(self) -> Agent:
        """Use this tool when the user needs to be redirected to other services or when the conversation needs to be routed to a different agent."""
        return Router(chat_ctx=self.chat_ctx)
    


class Quiz(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        prompt = agent_prompt('quiz')
        if chat_ctx is None:
            chat_ctx = ChatContext()
        super().__init__(instructions=prompt, chat_ctx=chat_ctx)

    async def on_enter(self) -> None:
        logger.info("Entering Quiz")
        await self.session.generate_reply(
            instructions=f"Greet the user and introduce yourself briefly as the Quiz agent."
        )

    @function_tool
    async def transfer_to_router(self) -> Agent:
        """Use this tool when the user needs to be redirected to other services or when the conversation needs to be routed to a different agent."""
        return Router(chat_ctx=self.chat_ctx)


class InsightsAgent(Agent):
    def __init__(self, chat_ctx: ChatContext = None):
        prompt = agent_prompt('insight')
        if chat_ctx is None:
            chat_ctx = ChatContext()
        super().__init__(instructions=prompt, chat_ctx=chat_ctx)

    async def on_enter(self) -> None:
        logger.info("Entering Insights")
        await self.session.generate_reply(
            instructions=f"Greet the user and introduce yourself briefly as the insights agent."
        )

    @function_tool
    async def transfer_to_router(self) -> Agent:
        """Use this tool when the user needs to be redirected to other services or when the conversation needs to be routed to a different agent."""
        return Router(chat_ctx=self.chat_ctx)

class CounsellingAgent(Agent):
    def __init__(self, chat_ctx: ChatContext = None):
        prompt = agent_prompt('counselling')
        if chat_ctx is None:
            chat_ctx = ChatContext()
        super().__init__(instructions=prompt, chat_ctx=chat_ctx)

    async def on_enter(self) -> None:
        logger.info("Entering Counselling")
        await self.session.generate_reply(
            instructions=f"Greet the user and introduce yourself briefly as the counselling agent."
        )

    @function_tool
    async def transfer_to_router(self) -> Agent:
        """Use this tool when the user needs to be redirected to other services or when the conversation needs to be routed to a different agent."""
        return Router(chat_ctx=self.chat_ctx)
    

class CourseAgent(Agent):
    def __init__(self, chat_ctx: ChatContext = None):
        prompt = agent_prompt('course')
        if chat_ctx is None:
            chat_ctx = ChatContext()
        super().__init__(instructions=prompt, chat_ctx=chat_ctx)

    async def on_enter(self) -> None:
        logger.info("Entering CourseAgent")
        await self.session.generate_reply(
            instructions=f"Greet the user and introduce yourself briefly as the Course enrollment agent."
        )

    @function_tool
    async def transfer_to_router(self) -> Agent:
        """Use this tool when the user needs to be redirected to other services or when the conversation needs to be routed to a different agent."""
        return Router(chat_ctx=self.chat_ctx)

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession[UserData](
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-live-001",
            voice="Zephyr",
            temperature=0.8,
            input_audio_transcription={},
            output_audio_transcription={},
            # modalities=["TEXT", "AUDIO"], 
        ),
        vad=silero.VAD.load(),
        userdata=UserData()
    )

    # Create the initial router agent - it will create its own chat context
    # router_agent = Router()
    router_agent = Engagement()

    await session.start(
        agent=router_agent,
        room=ctx.room,
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
