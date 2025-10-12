// ===============================================
// Simple Todo List Application
// ===============================================

// Utility functions
function generateId() {
    return '_' + Math.random().toString(36).substr(2, 9);
}

function saveToLocalStorage(key, data) {
    localStorage.setItem(key, JSON.stringify(data));
}

function loadFromLocalStorage(key) {
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : [];
}

// Task class representing a single todo item
class Task {
    constructor(title, description, dueDate, priority = 'normal') {
        this.id = generateId();
        this.title = title;
        this.description = description;
        this.dueDate = dueDate;
        this.priority = priority;
        this.completed = false;
        this.createdAt = new Date().toISOString();
    }

    toggleComplete() {
        this.completed = !this.completed;
    }

    updateDetails(newTitle, newDescription, newDueDate, newPriority) {
        this.title = newTitle;
        this.description = newDescription;
        this.dueDate = newDueDate;
        this.priority = newPriority;
    }
}

// TaskManager class to handle multiple tasks
class TaskManager {
    constructor(storageKey = 'tasks') {
        this.storageKey = storageKey;
        this.tasks = loadFromLocalStorage(this.storageKey);
    }

    addTask(task) {
        this.tasks.push(task);
        this._save();
    }

    deleteTask(taskId) {
        this.tasks = this.tasks.filter(t => t.id !== taskId);
        this._save();
    }

    getTask(taskId) {
        return this.tasks.find(t => t.id === taskId);
    }

    toggleTask(taskId) {
        const task = this.getTask(taskId);
        if (task) {
            task.toggleComplete();
            this._save();
        }
    }

    updateTask(taskId, title, desc, date, priority) {
        const task = this.getTask(taskId);
        if (task) {
            task.updateDetails(title, desc, date, priority);
            this._save();
        }
    }

    clearCompleted() {
        this.tasks = this.tasks.filter(t => !t.completed);
        this._save();
    }

    _save() {
        saveToLocalStorage(this.storageKey, this.tasks);
    }

    getAllTasks() {
        return this.tasks;
    }

    filterTasks(filterType) {
        switch (filterType) {
            case 'completed':
                return this.tasks.filter(t => t.completed);
            case 'pending':
                return this.tasks.filter(t => !t.completed);
            default:
                return this.tasks;
        }
    }
}

// UI handling
class UI {
    constructor(taskManager) {
        this.taskManager = taskManager;
        this.taskList = document.getElementById('task-list');
        this.addForm = document.getElementById('add-task-form');
        this.filterSelect = document.getElementById('filter');

        this._init();
    }

    _init() {
        this.addForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const title = document.getElementById('title').value.trim();
            const desc = document.getElementById('description').value.trim();
            const date = document.getElementById('due-date').value;
            const priority = document.getElementById('priority').value;

            if (title) {
                const task = new Task(title, desc, date, priority);
                this.taskManager.addTask(task);
                this._render();
                this.addForm.reset();
            }
        });

        this.filterSelect.addEventListener('change', () => this._render());
        this._render();
    }

    _render() {
        const filterType = this.filterSelect.value;
        const tasks = this.taskManager.filterTasks(filterType);
        this.taskList.innerHTML = '';

        tasks.forEach(task => {
            const li = document.createElement('li');
            li.className = `task-item ${task.completed ? 'completed' : ''}`;
            li.innerHTML = `
                <div>
                    <h3>${task.title}</h3>
                    <p>${task.description}</p>
                    <small>Due: ${task.dueDate || 'N/A'} | Priority: ${task.priority}</small>
                </div>
                <div>
                    <button class="toggle">${task.completed ? 'Undo' : 'Complete'}</button>
                    <button class="delete">Delete</button>
                </div>
            `;

            li.querySelector('.toggle').addEventListener('click', () => {
                this.taskManager.toggleTask(task.id);
                this._render();
            });

            li.querySelector('.delete').addEventListener('click', () => {
                this.taskManager.deleteTask(task.id);
                this._render();
            });

            this.taskList.appendChild(li);
        });
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    const manager = new TaskManager();
    new UI(manager);
});
