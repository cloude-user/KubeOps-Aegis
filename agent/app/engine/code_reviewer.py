import os
import sys
import json
import logging
from typing import Dict, Any, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from agent.app.core.config import settings

logger = logging.getLogger("aegis.reviewer")


class AICodeReviewerAgent:
    """AI Agent for Automated GitHub Pull Request Code & Security Review."""

    def __init__(self):
        self.llm = self._init_llm()

    def _init_llm(self):
        try:
            if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
                from langchain_openai import AzureChatOpenAI
                return AzureChatOpenAI(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    temperature=0.1
                )
            elif settings.OPENAI_API_KEY:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=settings.AI_MODEL_NAME, api_key=settings.OPENAI_API_KEY)
            elif settings.GEMINI_API_KEY:
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=settings.GEMINI_API_KEY)
            return None
        except Exception as e:
            logger.warning("Could not initialize LLM for code reviewer: %s", e)
            return None

    def review_git_diff(self, diff_text: str) -> str:
        """Perform automated AI code review on a Git pull request diff."""
        if not diff_text.strip():
            return "✅ No code changes detected in Pull Request."

        if self.llm:
            try:
                system_prompt = SystemMessage(content=(
                    "You are an expert AI Cloud Architect, SRE, and Security Reviewer. "
                    "Analyze the provided Git diff for Azure Infrastructure, Python code, and Kubernetes manifests. "
                    "Provide a structured code review markdown with:\n"
                    "1. 🔒 **Security & Vulnerability Audit**\n"
                    "2. ⚡ **Performance & Resource Optimization**\n"
                    "3. ☸️ **Kubernetes & Terraform Best Practices**\n"
                    "4. 💡 **Suggested Code Improvements**"
                ))
                user_prompt = HumanMessage(content=f"Git Diff:\n{diff_text[:8000]}")
                response = self.llm.invoke([system_prompt, user_prompt])
                return response.content
            except Exception as e:
                logger.error("LLM evaluation failed during PR review: %s", e)

        # Rule Engine Fallback
        review_comments = ["### 🤖 AI Code Reviewer Agent Summary\n"]
        if "eval(" in diff_text or "exec(" in diff_text:
            review_comments.append("⚠️ **Security Warning**: Avoid dynamic python code execution (`eval`/`exec`).")
        if "0.0.0.0/0" in diff_text:
            review_comments.append("⚠️ **Network Security**: Overly permissive firewall rule (`0.0.0.0/0`) detected.")
        if "limits:" not in diff_text and "kind: Deployment" in diff_text:
            review_comments.append("⚠️ **K8s Best Practice**: Container missing resource CPU/Memory limits.")
        if len(review_comments) == 1:
            review_comments.append("✅ Code review passed with zero critical security or configuration warnings.")

        return "\n\n".join(review_comments)


if __name__ == "__main__":
    diff_file = sys.argv[1] if len(sys.argv) > 1 else None
    diff_data = ""
    if diff_file and os.path.exists(diff_file):
        with open(diff_file, "r", encoding="utf-8") as f:
            diff_data = f.read()
    else:
        diff_data = sys.stdin.read() if not sys.stdin.isatty() else ""

    agent = AICodeReviewerAgent()
    review_output = agent.review_git_diff(diff_data)
    print(review_output)
