export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    if (request.headers.get("X-API-Key") !== env.API_KEY) {
       return new Response("Unauthorized", { status: 401 });
    }

    const data = await request.json();

    const discordPayload = 
      typeof data.message === "object"
        ? data.message
        : { content: data.message || "No message provided" }

    const response = await fetch(env.DISCORD_WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(discordPayload)
    });

    if (!response.ok) {
      return new Response("Failed to send to Discord", { status: 500 });
    }

    return new Response("Message forwarded", { status: 200 });
  }
};
