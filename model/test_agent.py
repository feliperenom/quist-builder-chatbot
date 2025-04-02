from agents import create_contact_agent

agent = create_contact_agent()
result = agent.invoke({"input": "My name is Felipe and my email is felipe@example.com"})

print("\n--- Resultado del agente ---")
print("Nombre:", result.get("name"))
print("Email:", result.get("email"))
print("¿Email enviado?", result.get("email_sent"))
if result.get("error"):
    print("❌ Error al enviar email:", result["error"])
