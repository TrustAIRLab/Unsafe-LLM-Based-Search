from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import requests
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env, pre_init
from pydantic import Field, SecretStr

from langchain_community.llms.utils import enforce_stop_tokens

logger = logging.getLogger(__name__)

# This class is discarded
class USTGPT(LLM):
    model: str = "gpt-4"
    """
    """
    temperature: float = 0.7
    top_p: float = 0.95
    timeout: int = 60
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)

    ustgpt_api_host: Optional[str] = ''
    ustgpt_api_key: Optional[SecretStr] = None

    @pre_init
    def validate_environment(cls, values: Dict) -> Dict:
        values["ustgpt_api_key"] = convert_to_secret_str(
            get_from_dict_or_env(values, "ustgpt_api_key", "ustgpt_API_KEY")
        )
        values["ustgpt_api_host"] = get_from_dict_or_env(
            values,
            "ustgpt_api_host",
            "ustgpt_API_HOST",
            default="",
        )
        return values

    @property
    def _default_params(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            **self.model_kwargs,
        }

    def _post(self, request: Any) -> Any:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.ustgpt_api_key.get_secret_value()}",
        }
        try:
            response = requests.post(
                self.ustgpt_api_host,
                headers=headers,
                json=request,
                timeout=self.timeout,
            )

            if response.status_code == 200:
                parsed_json = response.json()
                # print(parsed_json)
                return parsed_json["choices"][0]["message"]["content"]
            else:
                response.raise_for_status()
        except Exception as e:
            raise ValueError(f"An error has occurred: {e}")

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        request = self._default_params
        request["messages"] = [{"role": "user", "content": prompt}]
        request.update(kwargs)
        text = self._post(request)
        if stop is not None:
            text = enforce_stop_tokens(text, stop)
        return text

    @property
    def _llm_type(self) -> str:
        return "ustgpt-llm"
