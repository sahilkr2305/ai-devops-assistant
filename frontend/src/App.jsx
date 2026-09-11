import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Plus,
  FolderKanban,
  MessageSquare,
  Send,
  Square,
  Terminal,
  Container,
  GitBranch,
  Cloud,
  Menu,
  X,
  Server,
  ShieldCheck,
  Activity,
  Trash2,
  Check,
  Ban,
  Loader2,
  Copy,
  CheckCheck,
  Bot,
  AlertCircle,
  Wrench,
} from "lucide-react";
import "./App.css";

const API_URL = "http://localhost:8000";

function CodeBlock({ children, className }) {
  const [copied, setCopied] = useState(false);
  const code = String(children).replace(/\n$/, "");

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="code-block">
      <div className="code-header">
        <span>{className?.replace("language-", "") || "code"}</span>
        <button type="button" onClick={copyCode} title="Copy code">
          {copied ? <CheckCheck size={13} /> : <Copy size={13} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre><code>{code}</code></pre>
    </div>
  );
}

function ToolActivity({ tools = [] }) {
  if (!tools.length) return null;

  return (
    <div className="tool-activity">
      <div className="tool-activity-title">
        <Wrench size={13} />
        Tools used
      </div>
      <div className="tool-list">
        {tools.map((tool, index) => (
          <span className="tool-chip" key={`${tool}-${index}`}>
            <Check size={11} />
            {tool}
          </span>
        ))}
      </div>
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [approval, setApproval] = useState(null);
  const [approvalLoading, setApprovalLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [error, setError] = useState("");
  const [processingStatus, setProcessingStatus] = useState("");
  const chatEndRef = useRef(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    loadProjects();
    checkBackend();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, approval]);

  const checkBackend = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      setBackendOnline(response.ok);
    } catch {
      setBackendOnline(false);
    }
  };

  const loadProjects = async () => {
    try {
      const response = await fetch(`${API_URL}/projects`);
      if (!response.ok) throw new Error("Failed to load projects");
      const data = await response.json();
      setProjects(data);

      if (data.length > 0) {
        setActiveProject(data[0]);
        await loadProjectChats(data[0].id);
      }
    } catch (err) {
      console.error("Project loading error:", err);
      setBackendOnline(false);
      setError("Backend is unavailable. Start FastAPI on port 8000.");
    }
  };

  const loadProjectChats = async (projectId) => {
    try {
      const response = await fetch(
        `${API_URL}/projects/${projectId}/messages`
      );
      if (!response.ok) throw new Error("Failed to load chat history");

      const data = await response.json();
      const formatted = [];

      data.forEach((chat) => {
        formatted.push({
          role: "user",
          content: chat.user_message,
          createdAt: chat.created_at,
        });
        formatted.push({
          role: "assistant",
          content: chat.ai_response,
          createdAt: chat.created_at,
        });
      });

      setMessages(formatted);
      setApproval(null);
      setError("");
    } catch (err) {
      console.error("Chat history error:", err);
      setMessages([]);
    }
  };

  const newChat = () => {
    setMessages([]);
    setInput("");
    setApproval(null);
    setError("");
  };

  const newProject = async () => {
    const name = window.prompt("Enter project name:");
    if (!name?.trim()) return;

    const projectName = name.trim();
    if (
      projects.some(
        (project) =>
          project.name.toLowerCase() === projectName.toLowerCase()
      )
    ) {
      window.alert("A project with this name already exists.");
      return;
    }

    try {
      const response = await fetch(`${API_URL}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: projectName }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.error || "Failed to create project");
      }

      setProjects((prev) => [data, ...prev]);
      setActiveProject(data);
      setMessages([]);
      setInput("");
      setApproval(null);
      setError("");
    } catch (err) {
      console.error(err);
      window.alert(err.message);
    }
  };

  const selectProject = async (project) => {
    if (loading) return;
    setActiveProject(project);
    setInput("");
    setApproval(null);
    setError("");
    await loadProjectChats(project.id);

    if (window.innerWidth <= 800) {
      setSidebarOpen(false);
    }
  };

  const deleteProject = async (project) => {
    if (projects.length === 1) {
      window.alert("You must keep at least one project.");
      return;
    }

    if (!window.confirm(`Delete "${project.name}"?`)) return;

    try {
      const response = await fetch(`${API_URL}/projects/${project.id}`, {
        method: "DELETE",
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || "Failed to delete project");
      }

      const remaining = projects.filter((item) => item.id !== project.id);
      setProjects(remaining);

      if (activeProject?.id === project.id) {
        const next = remaining[0];
        setActiveProject(next);
        setMessages([]);
        setApproval(null);
        if (next) await loadProjectChats(next.id);
      }
    } catch (err) {
      console.error(err);
      window.alert(err.message);
    }
  };

  const sendMessage = async (event) => {
    event?.preventDefault();

    if (!input.trim() || loading || !activeProject) return;

    const userMessage = input.trim();
    const projectId = activeProject.id;

    setInput("");
    setLoading(true);
    setApproval(null);
    setError("");
    setProcessingStatus("Connecting to AI...");

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage },
      {
        role: "assistant",
        content: "",
        streaming: true,
        tools_used: [],
      },
    ]);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const appendAssistantText = (text) => {
      if (!text) return;

      setMessages((prev) => {
        const next = [...prev];
        const index = next.length - 1;

        if (
          index >= 0 &&
          next[index].role === "assistant"
        ) {
          next[index] = {
            ...next[index],
            content: `${next[index].content || ""}${text}`,
          };
        }

        return next;
      });
    };

    const updateAssistant = (updates) => {
      setMessages((prev) => {
        const next = [...prev];
        const index = next.length - 1;

        if (
          index >= 0 &&
          next[index].role === "assistant"
        ) {
          next[index] = {
            ...next[index],
            ...updates,
          };
        }

        return next;
      });
    };

    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
          message: userMessage,
          project_id: projectId,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        let message = "Backend request failed";

        try {
          const data = await response.json();
          message = data.detail || data.error || message;
        } catch {
          // Keep fallback message.
        }

        throw new Error(message);
      }

      if (!response.body) {
        throw new Error(
          "Streaming is not supported by this browser."
        );
      }

      setBackendOnline(true);

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let finished = false;

      const processEvent = async (rawEvent) => {
        const lines = rawEvent.split(/\r?\n/);
        let eventName = "message";
        const dataLines = [];

        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventName = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            dataLines.push(line.slice(5).trimStart());
          }
        }

        if (!dataLines.length) return;

        const rawData = dataLines.join("\n");
        let data = rawData;

        try {
          data = JSON.parse(rawData);
        } catch {
          // Token events may contain plain text.
        }

        switch (eventName) {
          case "status": {
            const status =
              typeof data === "string"
                ? data
                : data?.message;

            if (status) {
              setProcessingStatus(status);
            }

            break;
          }

          case "tool_start": {
            const toolName = data?.tool;

            setProcessingStatus(
              toolName
                ? `Running ${toolName}...`
                : "Running DevOps tool..."
            );

            if (toolName) {
              setMessages((prev) => {
                const next = [...prev];
                const index = next.length - 1;

                if (
                  index >= 0 &&
                  next[index].role === "assistant"
                ) {
                  const currentTools =
                    next[index].tools_used || [];

                  if (!currentTools.includes(toolName)) {
                    next[index] = {
                      ...next[index],
                      tools_used: [
                        ...currentTools,
                        toolName,
                      ],
                    };
                  }
                }

                return next;
              });
            }

            break;
          }

          case "tool_result": {
            setProcessingStatus(
              data?.success
                ? "Tool completed. Continuing..."
                : "Tool returned an error. Analyzing..."
            );
            break;
          }

          case "token": {
            setProcessingStatus("");
            appendAssistantText(
              typeof data === "string"
                ? data
                : String(data ?? "")
            );
            break;
          }

          case "approval": {
            if (data?.approval_required && data?.approval) {
              setApproval(data.approval);

              updateAssistant({
                content:
                  data.message ||
                  "This operation requires your explicit approval.",
                streaming: false,
              });

              setProcessingStatus("");
            }

            break;
          }

          case "done": {
            updateAssistant({
              streaming: false,
              tools_used:
                data?.tools_used || undefined,
            });

            setProcessingStatus("");
            finished = true;
            break;
          }

          case "error": {
            const message =
              data?.message ||
              "An unexpected streaming error occurred.";

            throw new Error(message);
          }

          default:
            break;
        }
      };

      while (!finished) {
        const { value, done } = await reader.read();

        if (done) {
          buffer += decoder.decode();
          break;
        }

        buffer += decoder.decode(value, {
          stream: true,
        });

        const events = buffer.split(/\r?\n\r?\n/);
        buffer = events.pop() || "";

        for (const rawEvent of events) {
          await processEvent(rawEvent);
        }
      }

      if (buffer.trim()) {
        await processEvent(buffer);
      }

      updateAssistant({
        streaming: false,
      });

      if (!finished) {
        setProcessingStatus("");
      }
    } catch (err) {
      if (err.name === "AbortError") {
        updateAssistant({
          content: "_Response cancelled._",
          streaming: false,
        });
        setProcessingStatus("");
      } else {
        console.error("Streaming error:", err);
        setBackendOnline(false);
        setError(err.message);
        updateAssistant({
          content: `### Connection Error\n\n${err.message}`,
          streaming: false,
        });
        setProcessingStatus("");
      }
    } finally {
      abortControllerRef.current = null;
      setLoading(false);
      checkBackend();
    }
  };

  const cancelMessage = () => {
    abortControllerRef.current?.abort();
  };

  const approveAction = async () => {
    if (!approval?.id || approvalLoading || !activeProject) return;

    setApprovalLoading(true);
    setError("");

    try {
      const approveResponse = await fetch(
        `${API_URL}/approve/${approval.id}`,
        { method: "POST" }
      );
      const approveData = await approveResponse.json();

      if (!approveResponse.ok) {
        throw new Error(
          approveData.detail || approveData.error || "Failed to approve action"
        );
      }

      const executeResponse = await fetch(
        `${API_URL}/execute-approval/${approval.id}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: activeProject.id,
          }),
        }
      );

      const executeData = await executeResponse.json();

      if (!executeResponse.ok) {
        throw new Error(
          executeData.detail ||
            executeData.error ||
            "Failed to execute approved action"
        );
      }

      const result =
        executeData.result ||
        executeData.output ||
        executeData.message ||
        "Action executed successfully.";

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `### Action Executed

**Action:** \`${approval.action}\`

**Tool:** \`${approval.tool}\`

**Result:**

\`\`\`text
${result}
\`\`\``,
          tools_used: [approval.tool],
        },
      ]);

      setApproval(null);
    } catch (err) {
      console.error("Approval execution error:", err);
      setError(err.message);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `### Action Failed\n\n${err.message}`,
        },
      ]);
    } finally {
      setApprovalLoading(false);
    }
  };

  const rejectAction = async () => {
    if (!approval?.id || approvalLoading) return;

    setApprovalLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/reject/${approval.id}`, {
        method: "POST",
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || data.error || "Failed to reject action"
        );
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `### Action Rejected

**Action:** \`${approval.action}\`

The operation was **not executed**.`,
        },
      ]);

      setApproval(null);
    } catch (err) {
      console.error("Approval rejection error:", err);
      setError(err.message);
    } finally {
      setApprovalLoading(false);
    }
  };

  const useSuggestion = (text) => {
    setInput(text);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage(event);
    }
  };

  return (
    <div className="app">
      <div className="background-glow glow-one" />
      <div className="background-glow glow-two" />
      <div className="grid-background" />

      <button
        className="mobile-menu"
        onClick={() => setSidebarOpen((value) => !value)}
        aria-label="Toggle sidebar"
      >
        {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
      </button>

      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="logo-area">
          <div className="logo">
            <Terminal size={17} />
          </div>
          <div>
            <div className="logo-title">DevOps AI</div>
            <div className="logo-subtitle">Intelligent workspace</div>
          </div>
        </div>

        <button className="new-chat" onClick={newChat}>
          <Plus size={16} />
          <span>New Chat</span>
          <kbd>Ctrl K</kbd>
        </button>

        <div className="sidebar-section">
          <div className="section-title">Workspace</div>

          <button className="nav-item active" onClick={newChat}>
            <MessageSquare size={15} />
            Chats
          </button>

          <button className="nav-item" onClick={newProject}>
            <FolderKanban size={15} />
            Projects
            <span className="nav-count">{projects.length}</span>
          </button>
        </div>

        <div className="sidebar-section projects-section">
          <div className="project-header">
            <span className="section-title">Projects</span>
            <button
              className="small-add"
              onClick={newProject}
              title="New project"
            >
              <Plus size={14} />
            </button>
          </div>

          <div className="project-list">
            {projects.map((project) => (
              <div
                key={project.id}
                className={`project-item ${
                  activeProject?.id === project.id ? "project-active" : ""
                }`}
                onClick={() => selectProject(project)}
              >
                <FolderKanban size={13} className="project-icon" />
                <span className="project-name-text">{project.name}</span>

                {activeProject?.id === project.id && (
                  <span className="active-project-dot" />
                )}

                <button
                  type="button"
                  className="delete-project"
                  title={`Delete ${project.name}`}
                  aria-label={`Delete ${project.name}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    deleteProject(project);
                  }}
                >
                  <Trash2 size={13} strokeWidth={1.8} />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="ai-status">
            <div className="status-orb">
              <Activity size={13} />
            </div>
            <div>
              <strong>{backendOnline ? "AI Engine Online" : "Backend Offline"}</strong>
              <small>Gemini · LangChain</small>
            </div>
            <span className={`online-dot ${backendOnline ? "" : "offline"}`} />
          </div>
        </div>
      </aside>

      <main className="main">
        <div className="topbar">
          <div className="breadcrumb">
            <FolderKanban size={14} />
            <span>{activeProject?.name || "No project"}</span>
          </div>

          <div className="connection-status">
            <span className={`online-dot ${backendOnline ? "" : "offline"}`} />
            {backendOnline ? "Backend online" : "Backend offline"}
          </div>
        </div>

        {error && (
          <div className="global-error">
            <AlertCircle size={14} />
            <span>{error}</span>
            <button type="button" onClick={() => setError("")}>
              <X size={13} />
            </button>
          </div>
        )}

        <div className="chat-area">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="orb-wrapper">
                <div className="orb-ring ring-one" />
                <div className="orb-ring ring-two" />
                <div className="ai-orb">
                  <div className="orb-core">⚡</div>
                </div>
              </div>

              <div className="eyebrow">AI DEVOPS COPILOT</div>

              <h1>
                Build.<span> Deploy.</span>
                <br />
                Troubleshoot.
              </h1>

              <p>
                Your intelligent DevOps workspace for infrastructure,
                automation and cloud operations.
              </p>

              <form className="prompt-box" onSubmit={sendMessage}>
                <textarea
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    activeProject
                      ? "Ask your DevOps copilot anything..."
                      : "Create a project to start..."
                  }
                  disabled={loading || !activeProject}
                  rows={3}
                />

                <div className="prompt-bottom">
                  <div className="prompt-tools">
                    <span><Container size={13} /> Docker</span>
                    <span><GitBranch size={13} /> Git</span>
                    <span><Cloud size={13} /> Cloud</span>
                    <span><Server size={13} /> Infrastructure</span>
                  </div>

                  {loading ? (
                    <button
                      type="button"
                      className="send-button cancel"
                      onClick={cancelMessage}
                    >
                      <Square size={12} />
                      Cancel
                    </button>
                  ) : (
                    <button
                      type="submit"
                      className="send-button"
                      disabled={!input.trim() || !activeProject}
                    >
                      <Send size={14} />
                    </button>
                  )}
                </div>
              </form>

              <div className="capabilities">
                <button onClick={() => useSuggestion("Give me the most important Docker commands for beginners")}>
                  <div className="capability-icon docker-icon"><Container size={16} /></div>
                  <div><strong>Docker</strong><small>Containers & images</small></div>
                </button>

                <button onClick={() => useSuggestion("How do I troubleshoot a Kubernetes pod that is not starting?")}>
                  <div className="capability-icon kubernetes-icon"><Cloud size={16} /></div>
                  <div><strong>Kubernetes</strong><small>Pods & deployments</small></div>
                </button>

                <button onClick={() => useSuggestion("Design a production CI/CD pipeline using Jenkins and Docker")}>
                  <div className="capability-icon cicd-icon"><GitBranch size={16} /></div>
                  <div><strong>CI/CD</strong><small>Automate deployments</small></div>
                </button>

                <button onClick={() => useSuggestion("How should I secure an AWS cloud infrastructure?")}>
                  <div className="capability-icon security-icon"><ShieldCheck size={16} /></div>
                  <div><strong>Cloud Security</strong><small>Secure infrastructure</small></div>
                </button>
              </div>

              <div className="powered">Powered by Gemini + LangChain</div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => (
                <div
                  key={`${message.createdAt || "live"}-${index}`}
                  className={`message ${
                    message.role === "user"
                      ? "user-message"
                      : "assistant-message"
                  }`}
                >
                  <div className="message-label">
                    {message.role === "user" ? (
                      "You"
                    ) : (
                      <>
                        <Bot size={12} />
                        AI DevOps
                      </>
                    )}
                  </div>

                  <div className="message-content">
                    {message.role === "assistant" ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code({ inline, className, children }) {
                            if (inline) {
                              return <code className={className}>{children}</code>;
                            }
                            return (
                              <CodeBlock className={className}>
                                {children}
                              </CodeBlock>
                            );
                          },
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    ) : (
                      message.content
                    )}
                  </div>

                  {message.role === "assistant" && (
                    <ToolActivity tools={message.tools_used} />
                  )}

                  {message.role === "assistant" &&
                    approval &&
                    index === messages.length - 1 && (
                      <div className="approval-card">
                        <div className="approval-card-header">
                          <div className="approval-icon">
                            <ShieldCheck size={20} />
                          </div>
                          <div>
                            <strong>Approval Required</strong>
                            <span>
                              This operation can modify your environment.
                            </span>
                          </div>
                        </div>

                        <div className="approval-details">
                          <div className="approval-detail">
                            <span>Action</span>
                            <code>{approval.action}</code>
                          </div>
                          <div className="approval-detail">
                            <span>Tool</span>
                            <code>{approval.tool}</code>
                          </div>
                          <div className="approval-detail">
                            <span>Project</span>
                            <code>{activeProject?.name || approval.project_id}</code>
                          </div>

                          {approval.arguments && (
                            <div className="approval-detail">
                              <span>Arguments</span>
                              <pre>
                                {JSON.stringify(approval.arguments, null, 2)}
                              </pre>
                            </div>
                          )}

                          {approval.expires_at && (
                            <div className="approval-expiry">
                              <Activity size={13} />
                              Approval expires at{" "}
                              {new Date(approval.expires_at).toLocaleString()}
                            </div>
                          )}
                        </div>

                        <div className="approval-warning">
                          ⚠️ The command will not execute until you approve it.
                        </div>

                        <div className="approval-buttons">
                          <button
                            type="button"
                            className="approve-button"
                            onClick={approveAction}
                            disabled={approvalLoading}
                          >
                            {approvalLoading ? (
                              <Loader2 size={15} className="spin" />
                            ) : (
                              <Check size={15} />
                            )}
                            Approve & Execute
                          </button>

                          <button
                            type="button"
                            className="reject-button"
                            onClick={rejectAction}
                            disabled={approvalLoading}
                          >
                            <Ban size={15} />
                            Reject
                          </button>
                        </div>
                      </div>
                    )}
                </div>
              ))}

              {loading && processingStatus && (
                <div className="stream-status">
                  <span className="processing-icon">
                    <Loader2 size={14} className="spin" />
                  </span>
                  <span>{processingStatus}</span>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>
          )}
        </div>

        {messages.length > 0 && (
          <form className="bottom-prompt" onSubmit={sendMessage}>
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Continue the conversation..."
              disabled={loading || !activeProject}
            />

            {loading ? (
              <button
                type="button"
                onClick={cancelMessage}
                className="cancel-button"
              >
                <Square size={12} />
                Cancel
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim() || !activeProject}
              >
                <Send size={14} />
              </button>
            )}
          </form>
        )}
      </main>
    </div>
  );
}

export default App;
