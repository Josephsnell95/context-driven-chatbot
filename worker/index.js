const systemPrompt = `${PERSONA}\n\n${EASTER_EGGS}\n\n${SUPPLEMENTARY_CONTEXT}\n\n${RULES}`;


export default {
    async fetch(request, env) {
        if (request.method === "OPTIONS") {
            return new Response(null, {
                headers: {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST",
                    "Access-Control-Allow-Headers": "Content-Type"
                }
            });
        }
        let messages;
        try {
            messages = await request.json();
        } catch {
            return new Response("Invalid request", { status: 400 });
        }
        let reply;
        let response;
        try {
            response = await env.AI.run("@cf/meta/llama-3.3-70b-instruct-fp8-fast", {
                messages: [
                { role: "system", content: systemPrompt },
                ...messages
                ]
            });
            reply = response.response;
        } catch (error) {
            if (error.code === 3036 || error.code === 3040) {
                const groqResponse = await fetch("https://api.groq.com/openai/v1/chat/completions", {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${env.GROQ_API_KEY}`,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        model: "llama-3.3-70b-versatile",
                        messages: [{ role: "system", content: systemPrompt }, ...messages]
                    })
                });
                if (groqResponse.status === 429) {
                    reply = "Joe's assistant is having a rest right now — why not reach out to him directly? You can find him on LinkedIn, X, and GitHub.";
                } else {
                    const groqData = await groqResponse.json();
                    reply = groqData.choices[0]?.message?.content
                        ?? "Joe's assistant is having a rest right now — why not reach out to him directly? You can find him on LinkedIn, X, and GitHub.";
                }
            } else {
                return new Response("Something went wrong", { status: 500 });
            }
        }
        return new Response(JSON.stringify({ reply: reply }), {
            headers: {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        });
    }
};