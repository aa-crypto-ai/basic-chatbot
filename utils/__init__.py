import os
from pathlib import PosixPath
import dotenv

path = PosixPath('~/.ai-agent-key/master.env').expanduser()
if not os.path.exists(path):
    raise Exception('~/.ai-agent-key/master.env not found, please run `cp sample.env ~/.ai-agent-key/master.env` and put your OpenRouter API key inside.')
dotenv.load_dotenv(path)
OPENROUTERAI_API_KEY = os.getenv('OPENROUTERAI_API_KEY')
