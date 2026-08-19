const state = {
  token: localStorage.getItem("taskflow_token"),
  user: null,
  tasks: [],
  filter: "all",
  authMode: "login",
};

if ("scrollRestoration" in history) history.scrollRestoration = "manual";

const element = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.token) headers.set("Authorization", `Bearer ${state.token}`);
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, { ...options, headers });
  if (response.status === 401 && path !== "/auth/login") logout();
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Não foi possível concluir a operação.");
  }
  return response.status === 204 ? null : response.json();
}

function setAuthMode(mode) {
  state.authMode = mode;
  const registering = mode === "register";
  element("name-field").classList.toggle("hidden", !registering);
  element("name").required = registering;
  element("auth-title").textContent = registering ? "Crie seu espaço" : "Bem-vindo de volta";
  element("auth-submit").textContent = registering ? "Criar conta" : "Entrar";
  element("login-tab").classList.toggle("active", !registering);
  element("register-tab").classList.toggle("active", registering);
  element("auth-error").textContent = "";
}

async function submitAuth(event) {
  event.preventDefault();
  const email = element("email").value;
  const password = element("password").value;
  element("auth-error").textContent = "";
  try {
    if (state.authMode === "register") {
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({ name: element("name").value, email, password }),
      });
    }
    const form = new URLSearchParams({ username: email, password });
    const token = await api("/auth/login", { method: "POST", body: form });
    state.token = token.access_token;
    localStorage.setItem("taskflow_token", state.token);
    await loadApplication();
  } catch (error) {
    element("auth-error").textContent = error.message;
  }
}

function logout() {
  state.token = null;
  state.user = null;
  state.tasks = [];
  localStorage.removeItem("taskflow_token");
  element("app-view").classList.add("hidden");
  element("auth-view").classList.remove("hidden");
  window.scrollTo(0, 0);
}

async function loadApplication() {
  try {
    [state.user, state.tasks] = await Promise.all([api("/auth/me"), api("/tasks")]);
    element("user-name").textContent = state.user.name;
    element("user-email").textContent = state.user.email;
    element("avatar").textContent = state.user.name.charAt(0).toUpperCase();
    element("auth-view").classList.add("hidden");
    element("app-view").classList.remove("hidden");
    window.scrollTo(0, 0);
    renderTasks();
  } catch (error) {
    logout();
  }
}

function visibleTasks() {
  if (state.filter === "open") return state.tasks.filter((task) => !task.is_completed);
  if (state.filter === "done") return state.tasks.filter((task) => task.is_completed);
  return state.tasks;
}

function renderTasks() {
  const completed = state.tasks.filter((task) => task.is_completed).length;
  const progress = state.tasks.length ? Math.round((completed / state.tasks.length) * 100) : 0;
  element("all-count").textContent = state.tasks.length;
  element("open-count").textContent = state.tasks.length - completed;
  element("done-count").textContent = completed;
  element("progress-value").textContent = `${progress}%`;
  element("progress-bar").style.width = `${progress}%`;
  element("progress-copy").textContent = state.tasks.length
    ? `${completed} de ${state.tasks.length} tarefas concluídas.`
    : "Comece criando sua primeira tarefa.";

  const tasks = visibleTasks();
  element("empty-state").classList.toggle("hidden", tasks.length > 0);
  element("task-list").innerHTML = tasks.map((task, index) => `
    <article class="task-card ${task.is_completed ? "done" : ""}" style="animation-delay:${index * 35}ms">
      <button class="complete-button" data-action="toggle" data-id="${task.id}" aria-label="${task.is_completed ? "Reabrir" : "Concluir"} tarefa">${task.is_completed ? "&#10003;" : ""}</button>
      <div><h3>${escapeHtml(task.title)}</h3><p>${escapeHtml(task.description || "Sem descrição")}</p></div>
      <div class="task-actions">
        <button data-action="edit" data-id="${task.id}" type="button">Editar</button>
        <button class="delete" data-action="delete" data-id="${task.id}" type="button">Excluir</button>
      </div>
    </article>`).join("");
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = value;
  return node.innerHTML;
}

function openTaskDialog(task = null) {
  element("task-id").value = task?.id || "";
  element("task-title").value = task?.title || "";
  element("task-description").value = task?.description || "";
  element("task-completed").checked = task?.is_completed || false;
  element("completed-field").classList.toggle("hidden", !task);
  element("dialog-title").textContent = task ? "Editar tarefa" : "Nova tarefa";
  element("task-error").textContent = "";
  element("task-dialog").showModal();
  element("task-title").focus();
}

async function submitTask(event) {
  event.preventDefault();
  const id = element("task-id").value;
  const payload = {
    title: element("task-title").value,
    description: element("task-description").value || null,
  };
  if (id) payload.is_completed = element("task-completed").checked;
  try {
    const task = await api(id ? `/tasks/${id}` : "/tasks", {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    if (id) state.tasks = state.tasks.map((item) => item.id === task.id ? task : item);
    else state.tasks.unshift(task);
    element("task-dialog").close();
    renderTasks();
  } catch (error) {
    element("task-error").textContent = error.message;
  }
}

async function handleTaskAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const id = Number(button.dataset.id);
  const task = state.tasks.find((item) => item.id === id);
  if (button.dataset.action === "edit") return openTaskDialog(task);
  try {
    if (button.dataset.action === "toggle") {
      const updated = await api(`/tasks/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_completed: !task.is_completed }),
      });
      state.tasks = state.tasks.map((item) => item.id === id ? updated : item);
    }
    if (button.dataset.action === "delete") {
      if (!window.confirm(`Excluir "${task.title}"?`)) return;
      await api(`/tasks/${id}`, { method: "DELETE" });
      state.tasks = state.tasks.filter((item) => item.id !== id);
    }
    renderTasks();
  } catch (error) {
    window.alert(error.message);
  }
}

element("today").textContent = new Intl.DateTimeFormat("pt-BR", { dateStyle: "full" }).format(new Date());
element("login-tab").addEventListener("click", () => setAuthMode("login"));
element("register-tab").addEventListener("click", () => setAuthMode("register"));
element("auth-form").addEventListener("submit", submitAuth);
element("logout").addEventListener("click", logout);
element("new-task").addEventListener("click", () => openTaskDialog());
element("task-form").addEventListener("submit", submitTask);
element("close-dialog").addEventListener("click", () => element("task-dialog").close());
element("cancel-task").addEventListener("click", () => element("task-dialog").close());
element("task-list").addEventListener("click", handleTaskAction);
document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => {
  state.filter = button.dataset.filter;
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item === button));
  renderTasks();
}));

if (state.token) loadApplication();