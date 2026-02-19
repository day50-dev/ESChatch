<img width="512" height="296" alt="eschatch_sm" src="https://github.com/user-attachments/assets/01fe229a-770c-4d94-9a2b-e73f1f99d0ae" />


**ESChatch** is a new concept, generally. It shepherds your input and output as a true wrapper and logs both sides of the conversation into files. Then when you invoke the llm it will pre-empt any existing interaction, kind of like the ssh shell escape. This is what the reversed triangle input in the video is. That's invoked with a keyboard shortcut, currently `ctrl+x`.

Then you type your command in and press enter. This command, plus the context of your previous input and output is then sent off to the llm and its response is wired up to the stdin of the application.

So for instance: 
 * Inside the `zsh` shell it gives shell commands.
 * Inside a full screen program, in this case `vim`. The vim session is pre-empted with a keystroke then just start typing. The llm infers it's vim and knows what mode it's in from the previous keystrokes and correctly exits.
 * Interactive Python is opened. It uses the context to infer it and responds appropriately.

This works seamlessly over ssh boundaries, in visual applications, at REPLs --- anywhere.

[ESChatch.webm](https://github.com/user-attachments/assets/29530ecf-15b6-4db1-9928-302c8674228e)
