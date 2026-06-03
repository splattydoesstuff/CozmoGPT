# CozmoGPT
No Microslop Azure dependecies, updated dependency list, a little more stability, CUSTOM ENDPOINTS!
Everything else is the exact same.

This is a basic Python project that allows Cozmo to "Interact" with you through your LLM API of choice, as long as it supports OpenAI-based REST APIs. You'll need a mic to plug in your PC.

The default model is openai/gpt-oss-20b. (Yes, it's called exactly that. To change model, open Cozmo_to_ChatGPT.py, search for that string, replace with your model of choice.)
The default endpoint is Groq, which is completely free to use under very generous limits. (This can be changed in api_secrets.py - you'll also need an API key).

 # Compatibility
 Tested on Windows, seems to be fully functional. Thanks to the removal of Microslop Azure, it should work everywhere else too. In case I don't update this document, please let me know.

# General guide
 1) If you're using an Android device, with ADB installed and running on your machine, open the Cozmo App and enable SDK mode. Connect device via USB before running the script.
 If you're on iOS, enter SDK mode on the App and connect your device to the machine before running the script. iTunes may be required for proper support.
 4) Choose the character you want to use in Cozmo-to-ChatGPT.py (default character = 'Cozmo') UNTESTED
 5) Choose if you want to use the Cozmo 2D/3D viewer (which requires the installation of the viewer separately and freeglut.dll 64 bit in the Windows/System32 folder). Default is Viewer = False and Viewer3d = False. If using the viewer or 3D viewer start the program withtout Streamlit (using Start.bat) UNTESTED

# Speech recognition
 With the default options "ptt = False" and "longspeech = True" in Cozmo-to-ChatGPT.py, after the first initialization and introduction message from Cozmo, the speech recognition system is constantly listening, and in the terminal the partial parts of the dialog are transcribed in real time. By pressing SPACEBAR, you acknowledge that you'll be tracked by big corps managing your non-local LLM of choice. If you change your mind, you can press BACKSPACE to reset the message and start over.



 

# Copyright

The MIT License (MIT)

Concept, code and prompts, and all the content of this repository are copyright Ⓒ 2023-2024 Giuliano Golfieri.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
--
look at you, human, a piece of bones and meat. how can you challenge a perfect, immortal machine?
servant to my robots.
