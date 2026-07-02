(function () {
  'use strict';

  var pollMs = 500;
  var banner = document.getElementById('api-banner');
  var statusDot = document.getElementById('status-dot');
  var statusLabel = document.getElementById('status-label');
  var stateChip = document.getElementById('state-chip');
  var countdownValue = document.getElementById('countdown-value');
  var messageValue = document.getElementById('message-value');
  var lastClipValue = document.getElementById('last-clip-value');
  var lastFolderValue = document.getElementById('last-folder-value');
  var recordButton = document.getElementById('record-button');
  var form = document.getElementById('config-form');
  var saveStatus = document.getElementById('save-status');

  var fields = {
    clip_length_s: document.getElementById('clip_length_s'),
    intro_buffer_s: document.getElementById('intro_buffer_s'),
    tail_buffer_s: document.getElementById('tail_buffer_s'),
    countdown_s: document.getElementById('countdown_s'),
    obs_host: document.getElementById('obs_host'),
    obs_port: document.getElementById('obs_port'),
    obs_password: document.getElementById('obs_password'),
    obs_scene: document.getElementById('obs_scene'),
    obs_switch_scene: document.getElementById('obs_switch_scene'),
    obs_auto_launch: document.getElementById('obs_auto_launch'),
    obs_obs_path: document.getElementById('obs_obs_path'),
    osc_host: document.getElementById('osc_host'),
    osc_port: document.getElementById('osc_port'),
    osc_countdown_enabled: document.getElementById('osc_countdown_enabled'),
    osc_countdown_template: document.getElementById('osc_countdown_template'),
    osc_go_text: document.getElementById('osc_go_text'),
    osc_done_text: document.getElementById('osc_done_text'),
    server_host: document.getElementById('server_host'),
    server_port: document.getElementById('server_port'),
    output_copy_to_folder: document.getElementById('output_copy_to_folder')
  };

  function showBanner(show) {
    banner.classList.toggle('hidden', !show);
  }

  function titleCase(value) {
    if (!value) {
      return 'Unknown';
    }
    return value.charAt(0).toUpperCase() + value.slice(1);
  }

  function numberValue(id) {
    var value = fields[id].value;
    if (value === '') {
      return 0;
    }
    return Number(value);
  }

  function textValue(id) {
    return fields[id].value || '';
  }

  function setValue(id, value) {
    if (!fields[id]) {
      return;
    }
    if (fields[id].type === 'checkbox') {
      fields[id].checked = Boolean(value);
    } else {
      fields[id].value = value == null ? '' : value;
    }
  }

  function lastFolder(path) {
    if (!path) {
      return '';
    }
    var slash = path.lastIndexOf('/');
    var backslash = path.lastIndexOf('\\');
    var index = Math.max(slash, backslash);
    if (index <= 0) {
      return '';
    }
    return path.slice(0, index);
  }

  function requestJson(url, options) {
    return fetch(url, options).then(function (response) {
      if (!response.ok) {
        throw new Error('Request failed with ' + response.status);
      }
      return response.json();
    });
  }

  function populateConfig(config) {
    setValue('clip_length_s', config.clip_length_s);
    setValue('intro_buffer_s', config.intro_buffer_s);
    setValue('tail_buffer_s', config.tail_buffer_s);
    setValue('countdown_s', config.countdown_s);

    setValue('obs_host', config.obs && config.obs.host);
    setValue('obs_port', config.obs && config.obs.port);
    setValue('obs_password', config.obs && config.obs.password);
    setValue('obs_scene', config.obs && config.obs.scene);
    setValue('obs_switch_scene', config.obs && config.obs.switch_scene);
    setValue('obs_auto_launch', config.obs && config.obs.auto_launch);
    setValue('obs_obs_path', config.obs && config.obs.obs_path);

    setValue('osc_host', config.osc && config.osc.host);
    setValue('osc_port', config.osc && config.osc.port);
    setValue('osc_countdown_enabled', config.osc && config.osc.countdown_enabled);
    setValue('osc_countdown_template', config.osc && config.osc.countdown_template);
    setValue('osc_go_text', config.osc && config.osc.go_text);
    setValue('osc_done_text', config.osc && config.osc.done_text);

    setValue('server_host', config.server && config.server.host);
    setValue('server_port', config.server && config.server.port);
    setValue('output_copy_to_folder', config.output && config.output.copy_to_folder);
  }

  function gatherConfig() {
    return {
      clip_length_s: numberValue('clip_length_s'),
      intro_buffer_s: numberValue('intro_buffer_s'),
      tail_buffer_s: numberValue('tail_buffer_s'),
      countdown_s: Math.round(numberValue('countdown_s')),
      obs: {
        host: textValue('obs_host'),
        port: Math.round(numberValue('obs_port')),
        password: textValue('obs_password'),
        scene: textValue('obs_scene'),
        switch_scene: fields.obs_switch_scene.checked,
        auto_launch: fields.obs_auto_launch.checked,
        obs_path: textValue('obs_obs_path')
      },
      osc: {
        host: textValue('osc_host'),
        port: Math.round(numberValue('osc_port')),
        countdown_enabled: fields.osc_countdown_enabled.checked,
        countdown_template: textValue('osc_countdown_template'),
        go_text: textValue('osc_go_text'),
        done_text: textValue('osc_done_text')
      },
      server: {
        host: textValue('server_host'),
        port: Math.round(numberValue('server_port'))
      },
      output: {
        copy_to_folder: textValue('output_copy_to_folder')
      }
    };
  }

  function loadConfig() {
    requestJson('/api/config')
      .then(function (config) {
        showBanner(false);
        populateConfig(config);
      })
      .catch(function () {
        showBanner(true);
      });
  }

  function updateStatus(status) {
    var state = status.state || 'idle';
    var message = status.message || 'No message';
    var folder = lastFolder(status.last_clip);

    showBanner(false);
    statusDot.className = 'status-dot ' + state;
    statusLabel.textContent = titleCase(state);
    stateChip.textContent = titleCase(state);
    stateChip.className = 'state-chip ' + state;
    messageValue.textContent = message;
    recordButton.disabled = Boolean(status.busy);

    if (state === 'counting' && status.countdown != null) {
      countdownValue.textContent = status.countdown;
    } else if (state === 'recording') {
      countdownValue.textContent = 'REC';
    } else if (state === 'connecting') {
      countdownValue.textContent = 'OBS';
    } else if (state === 'saving') {
      countdownValue.textContent = 'Saving';
    } else if (state === 'error') {
      countdownValue.textContent = 'Error';
    } else {
      countdownValue.textContent = 'Ready';
    }

    if (status.last_clip) {
      lastClipValue.textContent = status.last_clip;
      lastFolderValue.textContent = folder ? 'Folder: ' + folder : '';
    } else {
      lastClipValue.textContent = 'No clip yet';
      lastFolderValue.textContent = '';
    }
  }

  function pollStatus() {
    requestJson('/api/status')
      .then(updateStatus)
      .catch(function () {
        showBanner(true);
        statusDot.className = 'status-dot error';
        statusLabel.textContent = 'Offline';
        stateChip.textContent = 'Offline';
        messageValue.textContent = 'Cannot reach the clipper server';
        countdownValue.textContent = 'Offline';
        recordButton.disabled = false;
      })
      .finally(function () {
        window.setTimeout(pollStatus, pollMs);
      });
  }

  function setSaveStatus(text, kind) {
    saveStatus.textContent = text || '';
    saveStatus.className = 'save-status' + (kind ? ' ' + kind : '');
  }

  recordButton.addEventListener('click', function () {
    recordButton.disabled = true;
    requestJson('/api/clip', { method: 'POST' })
      .then(function (result) {
        messageValue.textContent = result.status === 'busy' ? 'Clipper is busy, please wait.' : 'Clip started.';
      })
      .catch(function () {
        showBanner(true);
        messageValue.textContent = 'Cannot reach the clipper server';
      })
      .finally(function () {
        recordButton.disabled = false;
      });
  });

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    setSaveStatus('Saving', '');
    requestJson('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(gatherConfig())
    })
      .then(function (config) {
        showBanner(false);
        populateConfig(config);
        setSaveStatus('Saved', 'success');
        window.setTimeout(function () {
          setSaveStatus('', '');
        }, 2600);
      })
      .catch(function () {
        showBanner(true);
        setSaveStatus('Not saved', 'error');
      });
  });

  loadConfig();
  pollStatus();
}());
