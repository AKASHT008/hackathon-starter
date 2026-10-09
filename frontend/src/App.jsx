
import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000/api/tasks";

function App() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadTasks() {
    try {
      const response = await fetch(API);
      if (!response.ok) throw new Error("Could not load tasks");
      setTasks(await response.json());
      setError("");
    } catch {
      setError("Unable to connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTasks();
  }, []);

  async function addTask(event) {
    event.preventDefault();
    if (!title.trim()) return;

    try {
      const response = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim() }),
      });
      if (!response.ok) throw new Error("Could not add task");
      setTitle("");
      await loadTasks();
    } catch {
      setError("Unable to add task. Please try again.");
    }
  }

  async function toggleTask(id) {
    try {
      const response = await fetch(`${API}/${id}`, {
        method: "PATCH",
      });
      if (!response.ok) throw new Error("Could not update task");
      await loadTasks();
    } catch {
      setError("Unable to update task.");
    }
  }

  async function deleteTask(id) {
    try {
      const response = await fetch(`${API}/${id}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Could not delete task");
      await loadTasks();
    } catch {
      setError("Unable to delete task.");
    }
  }

  return (
    <main style={{
      maxWidth: 650,
      margin: "50px auto",
      padding: 24,
      fontFamily: "Arial, sans-serif",
    }}>
      <h1>My Task Manager</h1>
      <p>React + FastAPI + MySQL</p>

      <form onSubmit={addTask} style={{ display: "flex", gap: 8 }}>
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Enter a task..."
          aria-label="Task title"
          style={{ flex: 1, padding: 12 }}
        />
        <button type="submit">Add task</button>
      </form>

      {error && <p role="alert">{error}</p>}
      {loading ? <p>Loading tasks...</p> : (
        <ul style={{ padding: 0, listStyle: "none" }}>
          {tasks.map((task) => (
            <li key={task.id} style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "12px 0",
              borderBottom: "1px solid #ddd",
            }}>
              <input
                type="checkbox"
                checked={Boolean(task.completed)}
                onChange={() => toggleTask(task.id)}
                aria-label={`Complete ${task.title}`}
              />
              <span style={{
                flex: 1,
                textDecoration: task.completed ? "line-through" : "none",
              }}>
                {task.title}
              </span>
              <button onClick={() => deleteTask(task.id)}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}

      {!loading && tasks.length === 0 && <p>No tasks yet. Add one above!</p>}
    </main>
  );
}

export default App;
