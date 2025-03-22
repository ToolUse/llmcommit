# 🎨 **Customization Guide**

This Blueprint is designed to be flexible and easily adaptable to your specific needs. This guide will walk you through some key areas you can customize to make the Blueprint your own.

---

## 🧠 **Changing the Model**

You can customize the AI models used by LLM Commit Generator:

### Jan AI Models (Default)

Set your preferred Jan AI model using the environment variable:

```bash
export JAN_MODEL="llama 3.1"  # or any other model you've downloaded
```

### Ollama Models

Set your preferred Ollama model using the environment variable:

```bash
export OLLAMA_MODEL="llama3.1"  # or any other model you've pulled
```

## 📝 **Modifying the System Prompt**

You can customize the prompt sent to the AI models by modifying the `generate_commit_messages` function in the `commit_generator.py` file. This allows you to:

- Change the number of commit messages generated
- Adjust the style or format of the messages
- Add specific guidelines for your team's commit message standards

## 💡 Other Customization Ideas

- Add support for additional AI providers
- Implement commit message templates
- Add integration with commit hooks
- Create organization-specific formatting rules

## 🤝 **Contributing to the Blueprint**

Want to help improve or extend this Blueprint? Check out the **[Future Features & Contributions Guide](future-features-contributions.md)** to see how you can contribute your ideas, code, or feedback to make this Blueprint even better!
