const taskSelect = document.getElementById("task-select");
const resetBtn = document.getElementById("reset-btn");
const stepBtn = document.getElementById("step-btn");
const taskTag = document.getElementById("task-tag");
const emailContent = document.getElementById("email-content");
const threadContainer = document.getElementById("thread-container");
const threadText = document.getElementById("thread-text");
const classificationSelect = document.getElementById("classification-select");
const replyInput = document.getElementById("reply-input");
const inputLabel = document.getElementById("input-label");
const stepFeedback = document.getElementById("step-feedback");
const metricTask = document.getElementById("metric-task");
const metricSteps = document.getElementById("metric-steps");
const metricAverage = document.getElementById("metric-average");
const metricLast = document.getElementById("metric-last");
const historyTable = document.querySelector("#history-table tbody");

const classificationOptions = {
  easy: ["spam", "not_spam"],
  medium: ["high", "medium", "low"],
};

function updateInputMode() {
  const task = taskSelect.value;
  taskTag.textContent = `Task: ${task}`;

  if (task === "hard") {
    classificationSelect.style.display = "none";
    replyInput.style.display = "block";
    inputLabel.textContent = "Reply Text";
    replyInput.placeholder = "Write a professional reply for this email...";
  } else {
    classificationSelect.style.display = "block";
    replyInput.style.display = "none";
    inputLabel.textContent = "Classification";
    classificationSelect.innerHTML = classificationOptions[task]
      .map((option) => `<option value="${option}">${option}</option>`)
      .join("");
  }
}

async function resetEnvironment() {
  stepFeedback.textContent = "Resetting environment...";
  const task = taskSelect.value;
  const response = await fetch("/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_level: task }),
  });

  if (!response.ok) {
    stepFeedback.textContent = `Reset failed: ${response.statusText}`;
    return;
  }

  const data = await response.json();
  updateObservation(data.observation);
  updateMetrics(data.metrics);
  historyTable.innerHTML = "";
  stepBtn.disabled = false;
  stepFeedback.textContent = "Environment reset. Ready for actions.";
}

function updateObservation(observation) {
  emailContent.textContent = observation.email_content;
  taskTag.textContent = `Task: ${observation.current_task}`;

  if (observation.thread_history && observation.thread_history.length) {
    threadContainer.hidden = false;
    threadText.textContent = observation.thread_history.join("\n");
  } else {
    threadContainer.hidden = true;
    threadText.textContent = "";
  }
}

function formatAction(task) {
  if (task === "hard") {
    return { classification: "", reply: replyInput.value.trim() };
  }
  return { classification: classificationSelect.value, reply: "" };
}

async function submitAction() {
  stepFeedback.textContent = "Submitting action...";
  const task = taskSelect.value;
  const action = formatAction(task);

  const response = await fetch("/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });

  if (!response.ok) {
    stepFeedback.textContent = `Step failed: ${response.statusText}`;
    return;
  }

  const data = await response.json();
  if (data.observation) {
    updateObservation(data.observation);
  }
  updateMetrics(data.metrics);
  addHistoryEntry(data.metrics.steps, task, action, data.reward);
  stepFeedback.textContent = `Score: ${data.reward.score}. ${data.reward.feedback}`;
  if (data.done) {
    stepBtn.disabled = true;
    stepFeedback.textContent += " Session complete.";
  }
}

function addHistoryEntry(step, task, action, reward) {
  const row = document.createElement("tr");
  const actionText = action.reply || action.classification || "n/a";
  row.innerHTML = `
    <td>${step}</td>
    <td>${task}</td>
    <td>${actionText}</td>
    <td>${reward.score.toFixed(2)}</td>
    <td>${reward.feedback}</td>
  `;
  historyTable.prepend(row);
}

function updateMetrics(metrics) {
  metricTask.textContent = metrics.task_level;
  metricSteps.textContent = metrics.steps;
  metricAverage.textContent = metrics.average_score.toFixed(2);
  metricLast.textContent = metrics.last_score !== null ? metrics.last_score.toFixed(2) : "N/A";
}

resetBtn.addEventListener("click", resetEnvironment);
stepBtn.addEventListener("click", submitAction);
taskSelect.addEventListener("change", () => {
  updateInputMode();
  stepFeedback.textContent = "Task changed. Press Reset to load task.";
  stepBtn.disabled = true;
});

updateInputMode();
