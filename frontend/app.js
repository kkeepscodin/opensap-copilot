const API = "http://127.0.0.1:8000";
const $ = id => document.getElementById(id);
const esc = value => String(value).replace(/[&<>"']/g, ch => ({
  "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
}[ch]));

async function checkApi(){
  try{
    const r = await fetch(`${API}/health`);
    const data = await r.json();
    if(!r.ok) throw new Error();
    $("apiStatus").textContent = `API ONLINE · v${data.version}`;
    $("apiStatus").className = "pill high";
  }catch{
    $("apiStatus").textContent = "API OFFLINE";
    $("apiStatus").className = "pill low";
  }
}
checkApi();

$("analyzeBtn").addEventListener("click", async () => {
  const file = $("fileInput").files[0];

  if(!file){
    $("message").textContent = "Choose an .abap or .txt file first.";
    return;
  }

  const form = new FormData();
  form.append("file", file);
  form.append("use_ai", $("useAi").checked ? "true" : "false");

  $("message").textContent = "Analyzing…";

  try{
    const response = await fetch(`${API}/api/v1/analyze`, {
      method: "POST",
      body: form
    });

    const data = await response.json();

    if(!response.ok){
      throw new Error(data.detail || "Analysis failed.");
    }

    render(data);
    $("message").textContent = "Analysis complete.";
  }catch(error){
    $("message").textContent = error.message;
  }
});

function render(data){
  $("results").hidden = false;
  $("programName").textContent = data.program_name;

  const grounded = data.grounded_conclusion;
  $("conclusion").textContent = grounded.conclusion;
  $("confidence").textContent = `${grounded.confidence.toUpperCase()} CONFIDENCE`;
  $("confidence").className = `pill ${grounded.confidence}`;
  $("mode").textContent = data.analysis_mode;

  $("evidence").innerHTML = grounded.evidence.map(item => `
    <div class="item">
      <b>✓ ${esc(item.value)}</b>
      <div class="muted">${esc(item.statement)}</div>
    </div>
  `).join("") || "<span class='muted'>No explicit evidence extracted.</span>";

  $("uncertainty").innerHTML = grounded.uncertainty
    .map(item => `<li>${esc(item)}</li>`)
    .join("");

  $("tables").innerHTML = data.tables.map(item => `
    <div class="item">
      <b>${esc(item.name)}</b> · ${esc(item.operation.toUpperCase())}
      <div class="muted">${esc(item.reason)}</div>
    </div>
  `).join("") || "<span class='muted'>None detected.</span>";

  $("dependencies").innerHTML = data.dependencies.map(item => `
    <div class="item">
      <b>${esc(item.name)}</b>
      <div class="muted">${esc(item.type)}</div>
    </div>
  `).join("") || "<span class='muted'>None detected.</span>";

  $("flow").innerHTML = data.call_flow
    .map(item => `<li>${esc(item)}</li>`)
    .join("");

  $("risks").innerHTML = data.risks.map(item => `
    <div class="item">
      <b>${esc(item.level.toUpperCase())}</b>
      <div class="muted">${esc(item.description)}</div>
    </div>
  `).join("");

  renderAi(data.ai_analysis);
}

function renderAi(ai){
  $("aiSection").hidden = false;
  $("aiStatus").textContent = ai.message;
  $("aiModel").textContent = ai.model
    ? `${ai.provider || "provider"} · ${ai.model}`
    : "AI not active";

  if(!ai.available){
    $("aiContent").hidden = true;
    return;
  }

  $("aiContent").hidden = false;
  $("aiTechnical").textContent = ai.technical_summary || "";
  $("aiBusiness").textContent = ai.business_summary || "";

  $("aiChanges").innerHTML = ai.change_considerations
    .map(item => `<li>${esc(item)}</li>`)
    .join("");

  $("aiUnknowns").innerHTML = ai.unknowns
    .map(item => `<li>${esc(item)}</li>`)
    .join("");

  $("aiEvidence").innerHTML = ai.used_evidence
    .map(item => `<span class="pill">${esc(item)}</span>`)
    .join(" ");

  const guard = $("groundingGuard");
  if(ai.grounding_guard_applied){
    guard.hidden = false;
    $("groundingNotes").innerHTML = ai.grounding_notes
      .map(item => `<li>${esc(item)}</li>`)
      .join("");
  }else{
    guard.hidden = true;
    $("groundingNotes").innerHTML = "";
  }
}
