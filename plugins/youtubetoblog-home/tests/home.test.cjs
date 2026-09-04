const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function load() {
  const notices = [];
  const context = {module: {exports: {}}, console: {error() {}, warn() {}},
    require: () => ({Plugin: class {}, ItemView: class {}, PluginSettingTab: class {},
      Notice: class {constructor(text) { notices.push(text); }}, normalizePath: s => s})};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../main.js'), 'utf8') + '\nmodule.exports.HomeView = HomeView;', context);
  return {Plugin: context.module.exports, notices};
}
function fixture() {
  const {Plugin, notices} = load();
  const calls = [];
  const opened = [];
  const plugin = {pipelineDefaults: () => ({rights: 'ask', mode: 'companion'}),
    ensureQueueNote: async () => ({created: true, path: '01 Queue/test.md'}),
    startInAgentClient: async prompt => {calls.push(prompt); return true;},
    openTarget: async target => opened.push(target.file)};
  const view = new Plugin.HomeView(null, plugin);
  view.input = {value: 'https://www.youtube.com/watch?v=abc123DEF45'};
  view.actionButtons = [{disabled: false}, {disabled: false}];
  return {Plugin, view, plugin, calls, opened, notices};
}

test('new video starts one full prompt', async () => {
  const f = fixture(); await f.view.process(false);
  assert.equal(f.calls.length, 1); assert.match(f.calls[0], /run full/);
  assert.equal(f.view.processing, false);
});
test('analyze only stops at brief', async () => {
  const f = fixture(); await f.view.process(true);
  assert.match(f.calls[0], /run analyze/); assert.match(f.calls[0], /stop after the brief/);
});
test('existing queue opens without new agent call or overriding rights', async () => {
  const f = fixture(); f.plugin.ensureQueueNote = async () => ({created: false, path: '01 Queue/existing.md'});
  f.view.rights = 'own'; f.view.mode = 'expand'; await f.view.process(false);
  assert.equal(f.calls.length, 0); assert.deepEqual(f.opened, ['01 Queue/existing.md']);
});
test('rapid double submission dispatches once', async () => {
  const f = fixture(); let release;
  f.plugin.ensureQueueNote = () => new Promise(resolve => {release = () => resolve({created: true, path: '01 Queue/test.md'});});
  const first = f.view.process(false); const second = f.view.process(false);
  release(); await Promise.all([first, second]); assert.equal(f.calls.length, 1);
});
test('same video in two views dispatches once', async () => {
  const f = fixture(); const other = new f.Plugin.HomeView(null, f.plugin); other.input = {value: f.view.input.value};
  let release; f.plugin.ensureQueueNote = () => new Promise(resolve => {release = () => resolve({created: true, path: '01 Queue/test.md'});});
  const first = f.view.process(false); await other.process(false); release(); await first;
  assert.equal(f.calls.length, 1);
});
test('write failure restores controls and never dispatches', async () => {
  const f = fixture(); f.plugin.ensureQueueNote = async () => {throw Error('write failed');};
  await f.view.process(false); assert.equal(f.calls.length, 0);
  assert.equal(f.view.processing, false); assert.ok(f.view.actionButtons.every(b => !b.disabled));
});
test('missing Agent Client opens the queue', async () => {
  const f = fixture(); f.plugin.startInAgentClient = async () => false;
  await f.view.process(false); assert.deepEqual(f.opened, ['01 Queue/test.md']);
});
test('invalid URL does not create a queue item', async () => {
  const f = fixture(); f.view.input.value = 'https://youtube.com.evil.test/watch?v=abc123DEF45';
  let writes = 0; f.plugin.ensureQueueNote = async () => {writes++;};
  await f.view.process(false); assert.equal(writes, 0); assert.equal(f.calls.length, 0);
});
test('pipeline defaults come from vault Settings', () => {
  const {Plugin} = load(); const p = new Plugin();
  p.app = {vault: {getFileByPath: () => ({})}, metadataCache: {getFileCache: () => ({frontmatter: {default_rights: 'third-party', default_mode: 'expand'}})}};
  assert.deepEqual(JSON.parse(JSON.stringify(p.pipelineDefaults())), {rights: 'third-party', mode: 'expand'});
});
test('blocked and done runs are not counted as active', () => {
  const {Plugin} = load(); const p = new Plugin();
  p.app = {vault: {getMarkdownFiles: () => ['blocked', 'done', 'writing'].map(status => ({path: '02 Videos/' + status + '/run.md', status}))},
    metadataCache: {getFileCache: file => ({frontmatter: {type: 'yt2b-video', status: file.status}})}};
  assert.equal(p.pipelineCounts().active, 1);
});
