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
} from "lucide-react";

import "./App.css";


const API_URL = "http://localhost:8000";


function App() {

  const [messages, setMessages] = useState([]);

  const [input, setInput] = useState("");

  const [loading, setLoading] = useState(false);

  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [projects, setProjects] = useState([]);

  const [activeProject, setActiveProject] =
    useState(null);

  const abortControllerRef = useRef(null);


  // ==================================================
  // LOAD PROJECTS
  // ==================================================

  useEffect(() => {

    loadProjects();

  }, []);


  const loadProjects = async () => {

    try {

      const response = await fetch(
        `${API_URL}/projects`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load projects"
        );
      }

      const data = await response.json();

      setProjects(data);

      if (data.length > 0) {

        setActiveProject(data[0]);

        loadProjectChats(data[0].id);

      }

    } catch (error) {

      console.error(
        "Project loading error:",
        error
      );

    }

  };


  // ==================================================
  // LOAD PROJECT CHAT HISTORY
  // ==================================================

  const loadProjectChats = async (
    projectId
  ) => {

    try {

      const response = await fetch(
        `${API_URL}/projects/${projectId}/chats`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load chat history"
        );
      }

      const data = await response.json();

      const formattedMessages = [];

      data.forEach((chat) => {

        formattedMessages.push({
          role: "user",
          content: chat.user_message,
        });

        formattedMessages.push({
          role: "assistant",
          content: chat.ai_response,
        });

      });

      setMessages(formattedMessages);

    } catch (error) {

      console.error(
        "Chat history error:",
        error
      );

      setMessages([]);

    }

  };


  // ==================================================
  // NEW CHAT
  // ==================================================

  const newChat = () => {

    setMessages([]);

    setInput("");

  };


  // ==================================================
  // CREATE PROJECT
  // ==================================================

  const newProject = async () => {

    const name = window.prompt(
      "Enter project name:"
    );

    if (!name || !name.trim()) {
      return;
    }

    const projectName = name.trim();


    const alreadyExists = projects.some(
      (project) =>
        project.name.toLowerCase() ===
        projectName.toLowerCase()
    );


    if (alreadyExists) {

      alert(
        "A project with this name already exists."
      );

      return;

    }


    try {

      const response = await fetch(
        `${API_URL}/projects`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            name: projectName,
          }),
        }
      );


      const data = await response.json();


      if (!response.ok) {

        throw new Error(
          data.error ||
          "Failed to create project"
        );

      }


      if (data.error) {

        alert(data.error);

        return;

      }


      setProjects((prev) => [
        ...prev,
        data,
      ]);


      setActiveProject(data);

      setMessages([]);

      setInput("");


    } catch (error) {

      console.error(error);

      alert(
        "Unable to create project. Make sure the backend is running."
      );

    }

  };


  // ==================================================
  // SELECT PROJECT
  // ==================================================

  const selectProject = async (
    project
  ) => {

    if (loading) {
      return;
    }

    setActiveProject(project);

    setInput("");

    await loadProjectChats(project.id);

  };


  // ==================================================
  // DELETE PROJECT
  // ==================================================

  const deleteProject = async (
    project
  ) => {

    if (projects.length === 1) {

      alert(
        "You must keep at least one project."
      );

      return;

    }


    const confirmed = window.confirm(
      `Delete "${project.name}"?`
    );


    if (!confirmed) {
      return;
    }


    try {

      const response = await fetch(
        `${API_URL}/projects/${project.id}`,
        {
          method: "DELETE",
        }
      );


      const data = await response.json();


      if (!response.ok) {

        throw new Error(
          data.error ||
          "Failed to delete project"
        );

      }


      if (data.error) {

        alert(data.error);

        return;

      }


      const remainingProjects =
        projects.filter(
          (item) =>
            item.id !== project.id
        );


      setProjects(
        remainingProjects
      );


      if (
        activeProject?.id ===
        project.id
      ) {

        const nextProject =
          remainingProjects[0];

        setActiveProject(
          nextProject
        );

        setMessages([]);

        setInput("");

        if (nextProject) {

          loadProjectChats(
            nextProject.id
          );

        }

      }


    } catch (error) {

      console.error(error);

      alert(
        "Unable to delete project."
      );

    }

  };


  // ==================================================
  // SEND MESSAGE
  // ==================================================

  const sendMessage = async (e) => {

    e.preventDefault();


    if (
      !input.trim() ||
      loading ||
      !activeProject
    ) {

      return;

    }


    const userMessage =
      input.trim();


    setMessages((prev) => [
      ...prev,

      {
        role: "user",
        content: userMessage,
      },

    ]);


    setInput("");

    setLoading(true);


    const controller =
      new AbortController();


    abortControllerRef.current =
      controller;


    try {

      const response = await fetch(
        `${API_URL}/chat`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            message: userMessage,

            project_id:
              activeProject.id,
          }),

          signal:
            controller.signal,
        }
      );


      const data =
        await response.json();


      if (!response.ok) {

        throw new Error(
          data.error ||
          "Backend request failed"
        );

      }


      if (data.error) {

        throw new Error(
          data.error
        );

      }


      setMessages((prev) => [
        ...prev,

        {
          role: "assistant",

          content:
            data.response,
        },

      ]);


    } catch (error) {

      if (
        error.name ===
        "AbortError"
      ) {

        setMessages((prev) => [
          ...prev,

          {
            role: "assistant",

            content:
              "_Response cancelled._",
          },

        ]);

      } else {

        console.error(error);

        setMessages((prev) => [
          ...prev,

          {
            role: "assistant",

            content:
              `❌ **Connection error**\n\n${error.message}`,
          },

        ]);

      }

    } finally {

      abortControllerRef.current =
        null;

      setLoading(false);

    }

  };


  // ==================================================
  // CANCEL MESSAGE
  // ==================================================

  const cancelMessage = () => {

    if (
      abortControllerRef.current
    ) {

      abortControllerRef.current.abort();

    }

  };


  // ==================================================
  // SUGGESTION
  // ==================================================

  const useSuggestion = (text) => {

    setInput(text);

  };


  // ==================================================
  // RENDER
  // ==================================================

  return (

    <div className="app">

      <div className="background-glow glow-one"></div>

      <div className="background-glow glow-two"></div>

      <div className="grid-background"></div>


      {/* MOBILE MENU */}

      <button
        className="mobile-menu"
        onClick={() =>
          setSidebarOpen(
            !sidebarOpen
          )
        }
      >

        {sidebarOpen ? (
          <X size={18} />
        ) : (
          <Menu size={18} />
        )}

      </button>


      {/* SIDEBAR */}

      <aside
        className={`sidebar ${
          sidebarOpen
            ? "sidebar-open"
            : ""
        }`}
      >

        {/* LOGO */}

        <div className="logo-area">

          <div className="logo">

            <Terminal size={17} />

          </div>


          <div>

            <div className="logo-title">
              DevOps AI
            </div>

            <div className="logo-subtitle">
              Intelligent workspace
            </div>

          </div>

        </div>


        {/* NEW CHAT */}

        <button
          className="new-chat"
          onClick={newChat}
        >

          <Plus size={16} />

          <span>
            New Chat
          </span>

          <kbd>
            ⌘ K
          </kbd>

        </button>


        {/* WORKSPACE */}

        <div className="sidebar-section">

          <div className="section-title">
            Workspace
          </div>


          <button
            className="nav-item active"
            onClick={newChat}
          >

            <MessageSquare
              size={15}
            />

            Chats

          </button>


          <button
            className="nav-item"
            onClick={newProject}
          >

            <FolderKanban
              size={15}
            />

            Projects

            <span className="nav-count">
              {projects.length}
            </span>

          </button>

        </div>


        {/* PROJECTS */}

        <div className="sidebar-section projects-section">

          <div className="project-header">

            <span className="section-title">
              Projects
            </span>


            <button
              className="small-add"
              onClick={newProject}
              title="New project"
            >

              <Plus size={14} />

            </button>

          </div>


          <div className="project-list">

            {projects.map(
              (project) => (

                <div
                  key={project.id}

                  className={`project-item ${
                    activeProject?.id ===
                    project.id
                      ? "project-active"
                      : ""
                  }`}

                  onClick={() =>
                    selectProject(
                      project
                    )
                  }
                >

                  <FolderKanban
                    size={13}
                    className="project-icon"
                  />


                  <span className="project-name-text">

                    {project.name}

                  </span>


                  {activeProject?.id ===
                    project.id && (

                    <span className="active-project-dot"></span>

                  )}


                  <button
                    type="button"

                    className="delete-project"

                    title={`Delete ${project.name}`}

                    aria-label={`Delete ${project.name}`}

                    onClick={(e) => {

                      e.stopPropagation();

                      deleteProject(
                        project
                      );

                    }}
                  >

                    <Trash2
                      size={13}
                      strokeWidth={1.8}
                    />

                  </button>

                </div>

              )
            )}

          </div>

        </div>


        {/* SIDEBAR STATUS */}

        <div className="sidebar-bottom">

          <div className="ai-status">

            <div className="status-orb">

              <Activity
                size={13}
              />

            </div>


            <div>

              <strong>
                AI Engine Online
              </strong>

              <small>
                Gemini · LangChain
              </small>

            </div>


            <span className="online-dot"></span>

          </div>

        </div>

      </aside>


      {/* MAIN */}

      <main className="main">


        {/* TOPBAR */}

        <div className="topbar">

          <div className="breadcrumb">

            <FolderKanban
              size={14}
            />

            <span>

              {activeProject?.name ||
                "Loading..."}

            </span>

          </div>


          <div className="connection-status">

            <span className="online-dot"></span>

            Online

          </div>

        </div>


        {/* CHAT */}

        <div className="chat-area">

          {messages.length === 0 ? (

            <div className="welcome">


              {/* AI ORB */}

              <div className="orb-wrapper">

                <div className="orb-ring ring-one"></div>

                <div className="orb-ring ring-two"></div>


                <div className="ai-orb">

                  <div className="orb-core">
                    ⚡
                  </div>

                </div>

              </div>


              {/* TITLE */}

              <div className="eyebrow">
                AI DEVOPS COPILOT
              </div>


              <h1>

                Build.

                <span>
                  {" "}Deploy.
                </span>

                <br />

                Troubleshoot.

              </h1>


              <p>

                Your intelligent DevOps
                workspace for infrastructure,
                automation and cloud operations.

              </p>


              {/* PROMPT */}

              <form
                className="prompt-box"
                onSubmit={sendMessage}
              >

                <textarea

                  value={input}

                  onChange={(e) =>
                    setInput(
                      e.target.value
                    )
                  }

                  onKeyDown={(e) => {

                    if (
                      e.key ===
                        "Enter" &&
                      !e.shiftKey
                    ) {

                      e.preventDefault();

                      sendMessage(e);

                    }

                  }}

                  placeholder="Ask your DevOps copilot anything..."

                  disabled={
                    loading ||
                    !activeProject
                  }

                  rows={3}

                />


                <div className="prompt-bottom">


                  <div className="prompt-tools">

                    <span>

                      <Container
                        size={13}
                      />

                      Docker

                    </span>


                    <span>

                      <GitBranch
                        size={13}
                      />

                      Git

                    </span>


                    <span>

                      <Cloud
                        size={13}
                      />

                      Cloud

                    </span>


                    <span>

                      <Server
                        size={13}
                      />

                      Infrastructure

                    </span>

                  </div>


                  {loading ? (

                    <button

                      type="button"

                      className="send-button cancel"

                      onClick={
                        cancelMessage
                      }

                    >

                      <Square
                        size={12}
                      />

                      Cancel

                    </button>

                  ) : (

                    <button

                      type="submit"

                      className="send-button"

                      disabled={
                        !input.trim() ||
                        !activeProject
                      }

                    >

                      <Send
                        size={14}
                      />

                    </button>

                  )}

                </div>

              </form>


              {/* CAPABILITIES */}

              <div className="capabilities">


                <button

                  onClick={() =>
                    useSuggestion(
                      "Give me the most important Docker commands for beginners"
                    )
                  }

                >

                  <div className="capability-icon docker-icon">

                    <Container
                      size={16}
                    />

                  </div>


                  <div>

                    <strong>
                      Docker
                    </strong>

                    <small>
                      Containers & images
                    </small>

                  </div>

                </button>


                <button

                  onClick={() =>
                    useSuggestion(
                      "How do I troubleshoot a Kubernetes pod that is not starting?"
                    )
                  }

                >

                  <div className="capability-icon kubernetes-icon">

                    <Cloud
                      size={16}
                    />

                  </div>


                  <div>

                    <strong>
                      Kubernetes
                    </strong>

                    <small>
                      Pods & deployments
                    </small>

                  </div>

                </button>


                <button

                  onClick={() =>
                    useSuggestion(
                      "Design a production CI/CD pipeline using Jenkins and Docker"
                    )
                  }

                >

                  <div className="capability-icon cicd-icon">

                    <GitBranch
                      size={16}
                    />

                  </div>


                  <div>

                    <strong>
                      CI/CD
                    </strong>

                    <small>
                      Automate deployments
                    </small>

                  </div>

                </button>


                <button

                  onClick={() =>
                    useSuggestion(
                      "How should I secure an AWS cloud infrastructure?"
                    )
                  }

                >

                  <div className="capability-icon security-icon">

                    <ShieldCheck
                      size={16}
                    />

                  </div>


                  <div>

                    <strong>
                      Cloud Security
                    </strong>

                    <small>
                      Secure infrastructure
                    </small>

                  </div>

                </button>

              </div>


              <div className="powered">

                Powered by Gemini + LangChain

              </div>

            </div>

          ) : (

            <div className="messages">

              {messages.map(
                (
                  message,
                  index
                ) => (

                  <div

                    key={index}

                    className={`message ${
                      message.role ===
                      "user"
                        ? "user-message"
                        : "assistant-message"
                    }`}

                  >

                    <div className="message-label">

                      {message.role ===
                      "user"
                        ? "You"
                        : "AI DevOps"}

                    </div>


                    <div className="message-content">

                      {message.role ===
                      "assistant" ? (

                        <ReactMarkdown
                          remarkPlugins={[
                            remarkGfm,
                          ]}
                        >

                          {
                            message.content
                          }

                        </ReactMarkdown>

                      ) : (

                        message.content

                      )}

                    </div>

                  </div>

                )
              )}


              {loading && (

                <div className="message assistant-message">

                  <div className="message-label">
                    AI DevOps
                  </div>


                  <div className="loading">

                    <span></span>

                    <span></span>

                    <span></span>

                  </div>

                </div>

              )}

            </div>

          )}

        </div>


        {/* BOTTOM PROMPT */}

        {messages.length > 0 && (

          <form

            className="bottom-prompt"

            onSubmit={sendMessage}

          >

            <input

              value={input}

              onChange={(e) =>
                setInput(
                  e.target.value
                )
              }

              placeholder="Continue the conversation..."

              disabled={loading}

            />


            {loading ? (

              <button

                type="button"

                onClick={
                  cancelMessage
                }

                className="cancel-button"

              >

                <Square
                  size={12}
                />

                Cancel

              </button>

            ) : (

              <button

                type="submit"

                disabled={
                  !input.trim() ||
                  !activeProject
                }

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