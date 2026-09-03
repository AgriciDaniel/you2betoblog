/* youtubetoblog Home: a landing page that replaces empty tabs.
   Plain JavaScript, no bundler. MIT. */

const { Plugin, ItemView, PluginSettingTab, Setting, Notice, setIcon, normalizePath } = require("obsidian");

const VIEW_TYPE = "youtubetoblog-home";
const SIDEBAR_VIEW_TYPE = "youtubetoblog-sidebar";
const AGENT_ID = "claude-code-acp";
const HOME_NOTE = "00 Home/Home.md";
const SETTINGS_NOTE = "00 Home/Settings.md";
const QUEUE_DIR = "01 Queue";
const SOURCES_NOTE = "01 Queue/Discovery/Sources.md";
const QUEUE_NOTE = "01 Queue/Queue.md";
const VIDEOS_NOTE = "02 Videos/Videos.md";
const BLOGS_NOTE = "03 Blogs/Blogs.md";
const APPROVALS_NOTE = "04 Approvals/Approvals.md";
const EVALUATIONS_NOTE = "05 Evaluations/Evaluations.md";
const BLOGS_DIR = "03 Blogs";
const WRITING_STUDIO_PROJECT_ID = "yt2b-blog-project";
const WRITING_STUDIO_PROJECT_PATH = BLOGS_DIR + "/_project.json";

const DEFAULT_SETTINGS = {
  wordmark: "you2toblog",
  defaultRights: "ask",
  defaultMode: "companion",
  replaceEmptyTabs: true,
  openSidebarOnStartup: true,
  showRecentRuns: true,
  writingStudioConfigured: false,
};

// Mirrors yt2b_common._YOUTUBE_PATTERNS: watch, youtu.be, shorts, live.
const YOUTUBE_PATTERNS = [
  /^https?:\/\/(?:www\.|m\.)?youtube\.com\/watch\?(?:[^#]*&)?v=([A-Za-z0-9_-]{11})(?:[&#].*)?$/,
  /^https?:\/\/youtu\.be\/([A-Za-z0-9_-]{11})(?:[?&#].*)?$/,
  /^https?:\/\/(?:www\.|m\.)?youtube\.com\/shorts\/([A-Za-z0-9_-]{11})(?:[?&#].*)?$/,
  /^https?:\/\/(?:www\.|m\.)?youtube\.com\/live\/([A-Za-z0-9_-]{11})(?:[?&#].*)?$/,
];

const PLAY_GLYPH =
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="44" height="44" aria-hidden="true">' +
  '<rect x="1" y="4" width="22" height="16" rx="5" fill="#FF0000"/>' +
  '<path d="M9.5 8.2v7.6l6.4-3.8z" fill="#FFFFFF"/></svg>';

const SHORTCUTS = [
  { label: "Home", icon: "house", open: { file: HOME_NOTE } },
  { label: "Feeds", icon: "rss", command: "rss-dashboard:open-dashboard" },
  { label: "Discover", icon: "compass", command: "rss-dashboard:open-discover" },
  { label: "Sources", icon: "library", open: { file: SOURCES_NOTE } },
  { label: "Queue", icon: "list-ordered", open: { file: QUEUE_NOTE } },
  { label: "Videos", icon: "clapperboard", open: { file: VIDEOS_NOTE } },
  { label: "Blogs", icon: "newspaper", open: { file: BLOGS_NOTE } },
  { label: "Approvals", icon: "check-square", open: { file: APPROVALS_NOTE } },
  { label: "Evaluations", icon: "bar-chart-3", open: { file: EVALUATIONS_NOTE } },
  { label: "Settings", icon: "settings", open: { file: SETTINGS_NOTE } },
];

const SIDEBAR_SHORTCUTS = [
  { label: "Feeds", icon: "rss", command: "rss-dashboard:open-dashboard" },
  { label: "Discover", icon: "compass", command: "rss-dashboard:open-discover" },
  { label: "Sources", icon: "library", open: { file: SOURCES_NOTE } },
  { label: "Queue", icon: "list-ordered", open: { file: QUEUE_NOTE } },
  { label: "Videos", icon: "clapperboard", open: { file: VIDEOS_NOTE } },
  { label: "Blogs", icon: "newspaper", open: { file: BLOGS_NOTE } },
  { label: "Approvals", icon: "check-square", open: { file: APPROVALS_NOTE } },
  { label: "Evaluations", icon: "bar-chart-3", open: { file: EVALUATIONS_NOTE } },
  { label: "Settings", icon: "settings", open: { file: SETTINGS_NOTE } },
];

function youtubeVideoId(url) {
  const text = (url || "").trim();
  for (const pattern of YOUTUBE_PATTERNS) {
    const m = pattern.exec(text);
    if (m) return m[1];
  }
  return null;
}

function watchUrl(videoId) {
  return "https://www.youtube.com/watch?v=" + videoId;
}

function today() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
}

// Same quoting rules as yt2b_common._dump_scalar.
function dumpScalar(value) {
  if (value === null || value === undefined) return '""';
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  const text = String(value);
  const needsQuotes =
    text === "" ||
    text !== text.trim() ||
    "[]{}#&*!|>'\"%@`-".includes(text[0]) ||
    text.includes(": ") ||
    text.endsWith(":") ||
    text.includes("\n");
  return needsQuotes ? JSON.stringify(text) : text;
}

function dumpFrontmatter(data) {
  const lines = [];
  for (const [key, value] of Object.entries(data)) {
    if (Array.isArray(value)) {
      if (value.length === 0) lines.push(key + ": []");
      else {
        lines.push(key + ":");
        for (const v of value) lines.push("  - " + dumpScalar(v));
      }
    } else {
      lines.push(key + ": " + dumpScalar(value));
    }
  }
  return lines.join("\n") + "\n";
}

function pipelinePrompt(notePath, watch, rights, mode, analyzeOnly) {
  const stage = analyzeOnly ? "analyze" : "full";
  const tail = analyzeOnly
    ? "then fetch, analyze in the background, segments and brief, then stop after the brief and tell me the run folder."
    : "then fetch, analyze in the background, segments, brief and strategy, create the strategy approval note and stop there and tell me its path.";
  return (
    "Use the youtube-to-blog skill: run " + stage + " for the queue note " + notePath +
    " (video " + watch + ", rights " + rights + ", mode " + mode + "). " +
    "Run doctor once, run setup first if BRAND.md or VOICE.md is missing at the vault root, " +
    tail + " Never publish, commit or push."
  );
}

class HomeView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
    this.navigation = false;
    this.rights = plugin.settings.defaultRights;
    this.mode = plugin.settings.defaultMode;
  }

  getViewType() { return VIEW_TYPE; }
  getDisplayText() { return this.plugin.settings.wordmark; }
  getIcon() { return "play"; }

  async onOpen() {
    this.render();
  }

  render() {
    const root = this.contentEl;
    root.empty();
    root.addClass("yt2b-home");
    const page = root.createDiv({ cls: "yt2b-home-page" });

    const header = page.createDiv({ cls: "yt2b-home-header" });
    const glyph = header.createDiv({ cls: "yt2b-home-glyph" });
    glyph.innerHTML = PLAY_GLYPH;
    header.createDiv({ cls: "yt2b-home-wordmark", text: this.plugin.settings.wordmark });

    this.input = page.createEl("input", {
      cls: "yt2b-home-input",
      type: "text",
      placeholder: "Paste a YouTube link",
    });
    this.input.spellcheck = false;
    this.input.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") { ev.preventDefault(); this.process(false); }
      if (ev.key === "Escape") { ev.preventDefault(); this.input.value = ""; }
    });

    const chips = page.createDiv({ cls: "yt2b-home-chips" });
    this.rightsChips = this.chipGroup(chips, ["ask", "own", "third-party"], this.rights, (v) => { this.rights = v; });
    this.modeChips = this.chipGroup(chips, ["companion", "expand"], this.mode, (v) => { this.mode = v; });

    const actions = page.createDiv({ cls: "yt2b-home-actions" });
    const processBtn = actions.createEl("button", { cls: "yt2b-home-primary", text: "Process" });
    processBtn.addEventListener("click", () => this.process(false));
    const analyzeBtn = actions.createEl("button", { cls: "yt2b-home-secondary", text: "Analyze only" });
    analyzeBtn.addEventListener("click", () => this.process(true));
    page.createDiv({ cls: "yt2b-home-hint", text: "Enter to process, Esc to clear" });

    const row = page.createDiv({ cls: "yt2b-home-shortcuts" });
    for (const item of SHORTCUTS) {
      const link = row.createDiv({ cls: "yt2b-home-shortcut" });
      link.setAttribute("role", "button");
      link.setAttribute("tabindex", "0");
      const icon = link.createDiv({ cls: "yt2b-home-shortcut-icon" });
      setIcon(icon, item.icon);
      link.createDiv({ cls: "yt2b-home-shortcut-label", text: item.label });
      const open = () => item.command
        ? this.plugin.runCommand(item.command, item.label)
        : this.plugin.openTarget(item.open);
      link.addEventListener("click", open);
      link.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); open(); } });
    }

    if (this.plugin.settings.showRecentRuns) this.renderRecent(page);
    window.setTimeout(() => this.input.focus(), 0);
  }

  chipGroup(parent, values, current, onPick) {
    const group = parent.createDiv({ cls: "yt2b-home-chip-group" });
    const buttons = [];
    for (const value of values) {
      const chip = group.createEl("button", { cls: "yt2b-home-chip", text: value });
      if (value === current) chip.addClass("is-active");
      chip.addEventListener("click", () => {
        buttons.forEach((b) => b.removeClass("is-active"));
        chip.addClass("is-active");
        onPick(value);
        this.input.focus();
      });
      buttons.push(chip);
    }
    return buttons;
  }

  renderRecent(page) {
    const runs = this.plugin.recentRuns(5);
    if (runs.length === 0) return;
    const list = page.createDiv({ cls: "yt2b-home-recent" });
    list.createDiv({ cls: "yt2b-home-recent-title", text: "Recent runs" });
    for (const run of runs) {
      const row = list.createDiv({ cls: "yt2b-home-recent-row" });
      row.createSpan({ cls: "yt2b-home-recent-name", text: run.title });
      row.createSpan({ cls: "yt2b-home-recent-status", text: run.status });
      row.createSpan({ cls: "yt2b-home-recent-date", text: run.updated });
      row.addEventListener("click", () => this.plugin.openTarget({ file: run.path }));
    }
  }

  async process(analyzeOnly) {
    const videoId = youtubeVideoId(this.input.value);
    if (!videoId) {
      new Notice("Paste a youtube.com/watch?v= link");
      return;
    }
    const watch = watchUrl(videoId);
    const result = await this.plugin.ensureQueueNote(videoId, watch, this.rights, this.mode);
    if (!result.created) new Notice("Already queued: " + result.path);
    this.input.value = "";
    const prompt = pipelinePrompt(result.path, watch, this.rights, this.mode, analyzeOnly);
    const started = await this.plugin.startInAgentClient(prompt);
    if (!started) {
      await this.plugin.openTarget({ file: result.path });
      new Notice("Queued. Install and enable Agent Client to start the pipeline from here; until then use the buttons on Home.", 8000);
    }
  }

  async onClose() {
    this.contentEl.empty();
  }
}

class SidebarView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
    this.navigation = false;
  }

  getViewType() { return SIDEBAR_VIEW_TYPE; }
  getDisplayText() { return "YouTube to blog"; }
  getIcon() { return "play"; }

  async onOpen() {
    this.render();
  }

  render() {
    const root = this.contentEl;
    root.empty();
    root.addClass("yt2b-sidebar");

    const header = root.createDiv({ cls: "yt2b-sidebar-header" });
    const glyph = header.createDiv({ cls: "yt2b-sidebar-glyph" });
    glyph.innerHTML = PLAY_GLYPH;
    const heading = header.createDiv();
    heading.createDiv({ cls: "yt2b-sidebar-title", text: "YouTube to blog" });
    heading.createDiv({ cls: "yt2b-sidebar-subtitle", text: "Discover, shape, publish" });

    const newChat = root.createEl("button", { cls: "yt2b-sidebar-primary", text: "New chat" });
    const chatIcon = newChat.createSpan({ cls: "yt2b-sidebar-button-icon" });
    newChat.prepend(chatIcon);
    setIcon(chatIcon, "message-square-plus");
    newChat.addEventListener("click", () => this.plugin.runCommand("agent-client:open-new-chat-view", "New chat"));

    const dashboard = root.createEl("button", { cls: "yt2b-sidebar-dashboard", text: "Open dashboard" });
    const dashboardIcon = dashboard.createSpan({ cls: "yt2b-sidebar-button-icon" });
    dashboard.prepend(dashboardIcon);
    setIcon(dashboardIcon, "play");
    dashboard.addEventListener("click", () => this.plugin.openHome());

    const queueSource = root.createEl("button", { cls: "yt2b-sidebar-source", text: "Queue open source" });
    const queueSourceIcon = queueSource.createSpan({ cls: "yt2b-sidebar-button-icon" });
    queueSource.prepend(queueSourceIcon);
    setIcon(queueSourceIcon, "list-plus");
    queueSource.addEventListener("click", () => this.plugin.queueActiveSource());

    root.createDiv({ cls: "yt2b-sidebar-section-label", text: "Workspace" });
    const nav = root.createDiv({ cls: "yt2b-sidebar-nav" });
    for (const item of SIDEBAR_SHORTCUTS) {
      const button = nav.createEl("button", { cls: "yt2b-sidebar-nav-item" });
      const icon = button.createSpan({ cls: "yt2b-sidebar-nav-icon" });
      setIcon(icon, item.icon);
      button.createSpan({ text: item.label });
      button.addEventListener("click", () => item.command
        ? this.plugin.runCommand(item.command, item.label)
        : this.plugin.openTarget(item.open));
    }

    const status = this.plugin.pipelineCounts();
    root.createDiv({ cls: "yt2b-sidebar-section-label", text: "At a glance" });
    const stats = root.createDiv({ cls: "yt2b-sidebar-stats" });
    this.stat(stats, status.queue, "Queued");
    this.stat(stats, status.active, "Active");
    this.stat(stats, status.approvals, "Approvals");
    this.stat(stats, status.blogs, "Blogs");

    const spacer = root.createDiv({ cls: "yt2b-sidebar-spacer" });
    spacer.setAttribute("aria-hidden", "true");
    const studio = root.createEl("button", { cls: "yt2b-sidebar-studio", text: "Writing Studio" });
    const studioIcon = studio.createSpan({ cls: "yt2b-sidebar-button-icon" });
    studio.prepend(studioIcon);
    setIcon(studioIcon, "feather");
    studio.addEventListener("click", () => this.plugin.runCommand("writing-studio:open-launcher", "Writing Studio"));
  }

  stat(parent, value, label) {
    const item = parent.createDiv({ cls: "yt2b-sidebar-stat" });
    item.createDiv({ cls: "yt2b-sidebar-stat-value", text: String(value) });
    item.createDiv({ cls: "yt2b-sidebar-stat-label", text: label });
  }

  async onClose() {
    this.contentEl.empty();
  }
}

class HomeSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();
    const save = async () => { await this.plugin.saveSettings(); this.plugin.refreshViews(); };

    new Setting(containerEl).setName("Wordmark").setDesc("Text next to the play glyph.")
      .addText((t) => t.setValue(this.plugin.settings.wordmark).onChange(async (v) => {
        this.plugin.settings.wordmark = v.trim() || DEFAULT_SETTINGS.wordmark; await save();
      }));
    new Setting(containerEl).setName("Default rights").setDesc("Preselected rights chip.")
      .addDropdown((d) => d.addOptions({ ask: "ask", own: "own", "third-party": "third-party" })
        .setValue(this.plugin.settings.defaultRights)
        .onChange(async (v) => { this.plugin.settings.defaultRights = v; await save(); }));
    new Setting(containerEl).setName("Default mode").setDesc("Preselected mode chip.")
      .addDropdown((d) => d.addOptions({ companion: "companion", expand: "expand" })
        .setValue(this.plugin.settings.defaultMode)
        .onChange(async (v) => { this.plugin.settings.defaultMode = v; await save(); }));
    new Setting(containerEl).setName("Replace empty tabs").setDesc("Every new empty tab becomes the landing page.")
      .addToggle((t) => t.setValue(this.plugin.settings.replaceEmptyTabs)
        .onChange(async (v) => { this.plugin.settings.replaceEmptyTabs = v; await save(); }));
    new Setting(containerEl).setName("Open dashboard sidebar on startup").setDesc("Make YouTube to blog the default left sidebar instead of Writing Studio.")
      .addToggle((t) => t.setValue(this.plugin.settings.openSidebarOnStartup)
        .onChange(async (v) => { this.plugin.settings.openSidebarOnStartup = v; await save(); }));
    new Setting(containerEl).setName("Show recent runs").setDesc("List the last five video runs under the shortcuts.")
      .addToggle((t) => t.setValue(this.plugin.settings.showRecentRuns)
        .onChange(async (v) => { this.plugin.settings.showRecentRuns = v; await save(); }));
  }
}

module.exports = class YoutubetoblogHome extends Plugin {
  async onload() {
    this.sidebarRefreshTimer = null;
    await this.loadSettings();
    this.registerView(VIEW_TYPE, (leaf) => new HomeView(leaf, this));
    this.registerView(SIDEBAR_VIEW_TYPE, (leaf) => new SidebarView(leaf, this));
    this.addSettingTab(new HomeSettingTab(this.app, this));
    this.addRibbonIcon("play", "Open youtubetoblog home", () => this.openHome());
    this.addCommand({ id: "open-home", name: "Open youtubetoblog home", callback: () => this.openHome() });
    this.addCommand({ id: "open-sidebar", name: "Open YouTube to blog sidebar", callback: () => this.openSidebar() });
    this.addCommand({ id: "queue-active-source", name: "Queue active saved source", callback: () => this.queueActiveSource() });
    this.registerEvent(this.app.workspace.on("layout-change", () => this.replaceEmptyLeaves()));
    this.registerEvent(this.app.vault.on("create", () => this.scheduleSidebarRefresh()));
    this.registerEvent(this.app.vault.on("modify", () => this.scheduleSidebarRefresh()));
    this.registerEvent(this.app.vault.on("delete", () => this.scheduleSidebarRefresh()));
    this.app.workspace.onLayoutReady(async () => {
      await this.configureWritingStudio();
      this.replaceEmptyLeaves();
      if (this.settings.openSidebarOnStartup) {
        await this.openSidebar();
      }
    });
  }

  onunload() {
    if (this.sidebarRefreshTimer !== null) window.clearTimeout(this.sidebarRefreshTimer);
    this.app.workspace.detachLeavesOfType(VIEW_TYPE);
    this.app.workspace.detachLeavesOfType(SIDEBAR_VIEW_TYPE);
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  refreshViews() {
    for (const leaf of this.app.workspace.getLeavesOfType(VIEW_TYPE)) {
      if (leaf.view instanceof HomeView) leaf.view.render();
    }
    for (const leaf of this.app.workspace.getLeavesOfType(SIDEBAR_VIEW_TYPE)) {
      if (leaf.view instanceof SidebarView) leaf.view.render();
    }
  }

  scheduleSidebarRefresh() {
    if (this.sidebarRefreshTimer !== null) window.clearTimeout(this.sidebarRefreshTimer);
    this.sidebarRefreshTimer = window.setTimeout(() => {
      this.sidebarRefreshTimer = null;
      for (const leaf of this.app.workspace.getLeavesOfType(SIDEBAR_VIEW_TYPE)) {
        if (leaf.view instanceof SidebarView) leaf.view.render();
      }
    }, 250);
  }

  // Same mechanism as Home Tab: an empty leaf gets our view type.
  replaceEmptyLeaves() {
    if (!this.settings.replaceEmptyTabs) return;
    this.app.workspace.iterateRootLeaves((leaf) => {
      if (leaf.getViewState().type === "empty") leaf.setViewState({ type: VIEW_TYPE });
    });
  }

  async openHome() {
    const existing = this.app.workspace.getLeavesOfType(VIEW_TYPE);
    const leaf = existing.length > 0 ? existing[0] : this.app.workspace.getLeaf("tab");
    await leaf.setViewState({ type: VIEW_TYPE, active: true });
    this.app.workspace.revealLeaf(leaf);
  }

  async openSidebar() {
    const existing = this.app.workspace.getLeavesOfType(SIDEBAR_VIEW_TYPE);
    if (existing.length > 0) {
      await this.app.workspace.revealLeaf(existing[0]);
      return;
    }
    const restoredStudio = [
      ...this.app.workspace.getLeavesOfType("writing-studio-launcher"),
      ...this.app.workspace.getLeavesOfType("writing-studio-binder"),
      ...this.app.workspace.getLeavesOfType("writing-studio-writing-log"),
    ];
    const leaf = restoredStudio.length > 0 ? restoredStudio[0] : this.app.workspace.getLeftLeaf(true);
    if (!leaf) {
      new Notice("Could not open the YouTube to blog sidebar.");
      return;
    }
    await leaf.setViewState({ type: SIDEBAR_VIEW_TYPE, active: true });
    await this.app.workspace.revealLeaf(leaf);
  }

  async configureWritingStudio() {
    const plugins = this.app.plugins && this.app.plugins.plugins;
    const studio = plugins && plugins["writing-studio"];
    if (!studio || !studio.projectManager || !studio.settings) return false;

    const folder = this.app.vault.getFolderByPath(BLOGS_DIR);
    if (!folder) await this.app.vault.createFolder(BLOGS_DIR);

    const settingsFile = this.app.vault.getFileByPath(SETTINGS_NOTE);
    const settingsCache = settingsFile && this.app.metadataCache.getFileCache(settingsFile);
    const author = String((settingsCache && settingsCache.frontmatter && settingsCache.frontmatter.author) || "");
    let projectFile = this.app.vault.getFileByPath(WRITING_STUDIO_PROJECT_PATH);
    if (!projectFile) {
      const stamp = today();
      const project = {
        id: WRITING_STUDIO_PROJECT_ID,
        title: "YouTube to Blog",
        type: "blog",
        author,
        created: stamp,
        modified: stamp,
        description: "Pipeline articles from 03 Blogs. Tags, links and publication state are owned by the YouTube to Blog pipeline.",
        folderPath: BLOGS_DIR,
        goals: {},
      };
      await this.app.vault.create(WRITING_STUDIO_PROJECT_PATH, JSON.stringify(project, null, 2) + "\n");
      projectFile = this.app.vault.getFileByPath(WRITING_STUDIO_PROJECT_PATH);
    }

    await studio.projectManager.loadProject(BLOGS_DIR);
    if (!this.settings.writingStudioConfigured) {
      studio.settings.openOnStartup = false;
      studio.settings.frontmatterAutoUpdate = false;
      studio.settings.appendToDailyNote = false;
      studio.settings.currentWritingMode = "none";
      studio.settings.activeProjectId = WRITING_STUDIO_PROJECT_ID;
      if (author && !studio.settings.authorName) studio.settings.authorName = author;
      studio.settings.removedProjectIds = (studio.settings.removedProjectIds || [])
        .filter((id) => id !== WRITING_STUDIO_PROJECT_ID);
      await studio.saveSettings();
      await studio.projectManager.setActiveProject(WRITING_STUDIO_PROJECT_ID);
      this.settings.writingStudioConfigured = true;
      await this.saveSettings();
    }
    return Boolean(projectFile);
  }

  async openTarget(target) {
    const file = this.app.vault.getFileByPath(normalizePath(target.file));
    if (!file) { new Notice("Not found: " + target.file); return; }
    const leaf = this.app.workspace.getLeaf(false);
    await leaf.openFile(file);
    if (target.view && leaf.view && leaf.view.getViewType() === "bases") {
      try {
        const state = leaf.getViewState();
        await leaf.setViewState(Object.assign({}, state, { state: Object.assign({}, state.state, { viewName: target.view }) }));
      } catch (err) {
        console.warn("[youtubetoblog Home] could not select Bases view", target.view, err);
      }
    }
  }

  async queueActiveSource() {
    const sourceFile = this.app.workspace.getActiveFile();
    const cache = sourceFile && this.app.metadataCache.getFileCache(sourceFile);
    const fm = cache && cache.frontmatter;
    if (!sourceFile || !fm || fm.type !== "yt2b-source") {
      new Notice("Open a saved YouTube source note first.");
      return;
    }
    const videoId = youtubeVideoId(String(fm.source_url || ""));
    if (!videoId) {
      new Notice("The open source does not contain a canonical YouTube URL.");
      return;
    }
    try {
      const watch = watchUrl(videoId);
      const result = await this.ensureQueueNote(
        videoId,
        watch,
        "ask",
        this.settings.defaultMode,
        sourceFile.path,
      );
      await this.linkSourceToQueue(sourceFile, result.path);
      await this.openTarget({ file: result.path });
      new Notice(result.created ? "Source promoted to the queue." : "Source linked to the existing queue item.");
    } catch (err) {
      console.error("[youtubetoblog Home] source promotion failed", err);
      new Notice("Could not link the source to the queue; see the console.");
    }
  }

  async linkSourceToQueue(sourceFile, queuePath) {
    const queueFile = this.app.vault.getFileByPath(normalizePath(queuePath));
    if (!queueFile) throw new Error("Queue note not found: " + queuePath);
    const sourceLink = this.app.fileManager.generateMarkdownLink(
      sourceFile,
      queueFile.path,
      undefined,
      "source",
    );
    const queueLink = this.app.fileManager.generateMarkdownLink(
      queueFile,
      sourceFile.path,
      undefined,
      "queue",
    );

    await this.app.fileManager.processFrontMatter(queueFile, (data) => {
      const current = Array.isArray(data.source_notes) ? data.source_notes.map(String) : [];
      if (!current.includes(sourceLink)) current.push(sourceLink);
      data.source_notes = current;
      data.discovered_via = "rss-dashboard";
      data.updated = today();
    });
    await this.app.fileManager.processFrontMatter(sourceFile, (data) => {
      data.queue = queueLink;
      data.status = "promoted";
      data.updated = today();
    });
  }

  runCommand(commandId, label) {
    const registry = this.app.commands && this.app.commands.commands;
    if (!registry || !registry[commandId]) {
      new Notice(label + " is unavailable. Check that its plugin is enabled.");
      return false;
    }
    return this.app.commands.executeCommandById(commandId);
  }

  recentRuns(limit) {
    const rows = [];
    for (const file of this.app.vault.getMarkdownFiles()) {
      if (!file.path.startsWith("02 Videos/")) continue;
      const cache = this.app.metadataCache.getFileCache(file);
      const fm = cache && cache.frontmatter;
      if (!fm || fm.type !== "yt2b-video") continue;
      rows.push({
        path: file.path,
        title: String(fm.title || file.parent.name),
        status: String(fm.status || ""),
        updated: String(fm.updated || ""),
        mtime: file.stat.mtime,
      });
    }
    rows.sort((a, b) => (b.updated.localeCompare(a.updated)) || (b.mtime - a.mtime));
    return rows.slice(0, limit);
  }

  pipelineCounts() {
    const counts = { queue: 0, active: 0, approvals: 0, blogs: 0 };
    for (const file of this.app.vault.getMarkdownFiles()) {
      const cache = this.app.metadataCache.getFileCache(file);
      const fm = cache && cache.frontmatter;
      if (!fm) continue;
      if (file.path.startsWith("01 Queue/") && fm.type === "yt2b-queue" && fm.status === "queued") counts.queue += 1;
      if (file.path.startsWith("02 Videos/") && fm.type === "yt2b-video" && fm.status !== "done" && fm.status !== "failed") counts.active += 1;
      if (file.path.startsWith("04 Approvals/") && fm.type === "yt2b-approval" && fm.status === "requested") counts.approvals += 1;
      if (file.path.startsWith("03 Blogs/") && !file.path.includes("/publish-kit/") && !file.path.includes("/.render/") && fm.type === "yt2b-blog") counts.blogs += 1;
    }
    return counts;
  }

  findQueueNote(videoId) {
    const folder = this.app.vault.getFolderByPath(QUEUE_DIR);
    if (!folder) return null;
    for (const child of folder.children) {
      if (!child.extension || child.extension !== "md") continue;
      const cache = this.app.metadataCache.getFileCache(child);
      const fm = cache && cache.frontmatter;
      if (fm && fm.type === "yt2b-queue" && fm.video_id === videoId) return child.path;
      if (child.basename.endsWith("-" + videoId)) return child.path;
    }
    return null;
  }

  async ensureQueueNote(videoId, watch, rights, mode, sourceNote = "") {
    const existing = this.findQueueNote(videoId);
    if (existing) return { path: existing, created: false };
    const stamp = today();
    const frontmatter = {
      type: "yt2b-queue",
      video_url: watch,
      video_id: videoId,
      rights: rights,
      mode: mode,
      priority: 3,
      status: "queued",
      run: "",
      note: sourceNote ? "from a saved source" : "from the landing page",
      source_notes: [],
      created: stamp,
      updated: stamp,
      discovered_via: sourceNote ? "rss-dashboard" : "home",
      tags: [
        "yt2b",
        "stage/queue",
        "format/video",
        "source/youtube",
        ...(rights === "own" || rights === "third-party" ? ["rights/" + rights] : []),
      ],
    };
    const body = sourceNote
      ? "[Watch on YouTube](" + watch + ") from a saved source\n"
      : "[Watch on YouTube](" + watch + ") from the landing page\n";
    const path = normalizePath(QUEUE_DIR + "/" + stamp + "-" + videoId + ".md");
    if (!this.app.vault.getFolderByPath(QUEUE_DIR)) await this.app.vault.createFolder(QUEUE_DIR);
    await this.app.vault.create(path, "---\n" + dumpFrontmatter(frontmatter) + "---\n" + body);
    new Notice("Queued " + path);
    return { path: path, created: true };
  }

  async startInAgentClient(prompt) {
    const agentClient = this.app.plugins && this.app.plugins.plugins && this.app.plugins.plugins["agent-client"];
    if (!agentClient || typeof agentClient.runPromptInChat !== "function") return false;
    try {
      await agentClient.runPromptInChat({
        agentId: AGENT_ID,
        prompt: prompt,
        autoSend: true,
        viewType: "right-pane",
        sourcePath: HOME_NOTE,
        lineStart: 0,
      });
      return true;
    } catch (err) {
      console.error("[youtubetoblog Home] Agent Client handoff failed", err);
      new Notice("Agent Client could not start the pipeline; see the console.");
      return false;
    }
  }
};
