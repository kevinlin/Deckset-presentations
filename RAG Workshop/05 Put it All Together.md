autoscale: true
footer: © Zühlke APAC SWEX+DX 2024
slidenumbers: true

# [fit] **_5_**

![](bg-symbols.jpeg)

---

# RAG Workshop - Put It All Together

## Estimated time: 60 minutes

### by _**Kevin Lin**_, _**Andreas Mueller**_

![](bg-rythem.jpeg)

---

# Task: Run the Frontend App

- Locate the pre-built frontend code in the `/frontend` folder.
- The frontend is built using **Angular**.

---

# Task: Run the Frontend App

## Install the necessary software

- Install the necessary software:
    - **Node.js**
    - **npm** (Node Package Manager)
    - **Angular CLI**
- These tools are needed to run the Angular app.

---

# Task: Run the Frontend App

## Running the Frontend App

- Start the Angular app:
- Run the following commands to install dependencies and start the app:

```bash
npm install # Or equivalent package manager command
npm start
```

- Check the app in your browser at:
  **`http://localhost:4200/`**

---

# Task: Integrate Frontend with Backend

- The frontend is pre-configured to communicate with the backend listening on:
  **`http://localhost:8000`**
- Check the **proxy settings** in `proxy.conf.json` to ensure proper routing.

---

# Task: Integrate Frontend with Backend

## Test the ChatBot

- Ask any questions related to the **insurance policy** in the chat window
- Use the debug console to check the **HTTP requests** and **responses**.

---

# Task: Integrate Frontend with Backend

## Troubleshooting Integration Issues

- Ensure that the backend server is running.
- Verify proxy settings in **proxy.conf.json** if requests fail.
- Checking the **console logs** for errors can provide additional insights.

---

# 🏆 Bonus Task: Improve Chat Experience

## Task: Context-Aware Chat and Streaming Responses

- Make the RAG application **context-aware** by including past chat conversations in the LLM prompt.

^ This helps maintain conversation context and provide a more fluid chat interaction.

---

# 🏆 Bonus Task: Collect User Feedback on Responses

## Collect User Feedback

- Implement simple controls like **Thumb Up** or **Thumb Down** for users to rate the chatbot's response.
- Feedback will help evaluate the quality of each response.

## Incorporate Feedback

- Think of ways to use feedback data to **improve response quality**.
- Example approaches:
    - Analyze **negative feedback** and adjust the **retrieval** or **generation** process.
    - Use **positive feedback** to reinforce successful response patterns.

^ Consider persisting the feedback together with the chat conversation to identify recurring issues or successes.

---

# 🏆 Bonus Task: Switching to Streaming Responses

- Switch to a **streaming approach** to make responses feel more interactive and improve user experience.
- This allows the user to see the response as it is generated, rather than waiting for the entire answer.


