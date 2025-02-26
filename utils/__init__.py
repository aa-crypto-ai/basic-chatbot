import os
import dotenv

if not os.path.exists('master.env'):
    raise Exception('master.env not found, please put your openrouter AI key inside: "OPENROUTERAI_API_KEY=sk-or-v1-a56691....."')
dotenv.load_dotenv('master.env')
OPENROUTERAI_API_KEY = os.getenv('OPENROUTERAI_API_KEY')
