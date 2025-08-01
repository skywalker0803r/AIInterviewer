let selectedJob = null;
let streamMode = "none";
let ws = null; // WebSocket instance
let mediaRecorder = null;
let audioChunks = [];

$(document).ready(function () {
  $('#search-btn').on('click', async function () {
    const keyword = $('#job-input').val().trim();
    if (!keyword) return alert("請輸入職缺名稱");

    $('#job-list').html("<p class='text-gray-500'>正在搜尋中...</p>");

    try {
      const res = await $.get(`http://127.0.0.1:8002/jobs?keyword=${encodeURIComponent(keyword)}`);
      const jobs = res.jobs;
      if (!jobs || jobs.length === 0) {
        $('#job-list').html("<p class='text-red-500'>查無職缺</p>");
        return;
      }

      const list = jobs.map((job, i) => `
        <div class="border p-3 rounded-lg cursor-pointer hover:bg-gray-100" data-index="${i}">
          <p class="font-bold">${job.title}</p>
          <p class="text-sm text-gray-600">${job.company}</p>
          <a href="${job.url}" target="_blank" class="text-blue-500 text-sm underline">查看職缺</a>
        </div>
      `).join('');

      $('#job-list').html(list);

      $('#job-list div').on('click', function () {
        const index = $(this).data('index');
        selectedJob = jobs[index];
        $('#selected-job').text(`✅ 已選擇職缺：${selectedJob.title} @ ${selectedJob.company}`);
      });

    } catch (err) {
      console.error("職缺搜尋失敗：", err);
      $('#job-list').html("<p class='text-red-500'>搜尋錯誤，請稍後再試</p>");
    }
  });

  $('#start-interview').on('click', async function () {
    if (!selectedJob) {
      alert("請先選擇一個職缺再開始面試");
      return;
    }

    // Disable the start button to prevent multiple clicks
    $('#start-interview').prop('disabled', true).text("面試進行中...");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamMode = "視訊 + 語音";
      $('#mode-label').text(`目前模式：${streamMode}`);
      $('#video-section').removeClass('hidden');
      document.getElementById('webcam').srcObject = stream;

      // Initialize WebSocket
      ws = new WebSocket("ws://127.0.0.1:8002/ws");

      ws.onopen = () => {
        console.log("WebSocket connected");
        // Send initial job info to backend via WebSocket if needed, or rely on initial POST
        // For now, we assume initial POST handles job setup

        // Start recording audio
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            ws.send(event.data); // Send audio chunk to backend
          }
        };
        mediaRecorder.start(1000); // Send data every 1 second
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.text) {
          appendToChat("🤖 AI 面試官", data.text);
        }
        if (data.audio_url) {
          $('#tts-audio').attr("src", data.audio_url)[0].play();
        }
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        if (mediaRecorder && mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
        }
        $('#start-interview').prop('disabled', false).text("開始模擬面試");
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        alert("WebSocket 連線錯誤，請檢查後端服務");
        if (mediaRecorder && mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
        }
        $('#start-interview').prop('disabled', false).text("開始模擬面試");
      };

    } catch (err) {
      console.warn("啟動視訊失敗，改用語音模式", err);
      try {
        const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamMode = "語音僅";
        $('#mode-label').text(`目前模式：${streamMode}`);

        // Initialize WebSocket for audio-only
        ws = new WebSocket("ws://127.0.0.1:8002/ws");

        ws.onopen = () => {
          console.log("WebSocket connected (audio-only)");
          mediaRecorder = new MediaRecorder(audioStream, { mimeType: 'audio/webm' });
          mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
              ws.send(event.data);
            }
          };
          mediaRecorder.start(1000);
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.text) {
            if (data.speaker === "你") {
              appendToChat("🗣️ 你", data.text);
            } else {
              appendToChat("🤖 AI 面試官", data.text);
            }
          }
          if (data.audio_url) {
            $('#tts-audio').attr("src", data.audio_url)[0].play();
          }
        };

        ws.onclose = () => {
          console.log("WebSocket disconnected (audio-only)");
          if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
          $('#start-interview').prop('disabled', false).text("開始模擬面試");
        };

        ws.onerror = (error) => {
          console.error("WebSocket error (audio-only):", error);
          alert("WebSocket 連線錯誤，請檢查後端服務");
          if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
          $('#start-interview').prop('disabled', false).text("開始模擬面試");
        };

      } catch (err2) {
        alert("❌ 無法取得麥克風或攝影機權限");
        $('#start-interview').prop('disabled', false).text("開始模擬面試");
        return;
      }
    }

    $('#chat-box').html("<p class='text-blue-500'>⏳ 等待 AI 面試官回覆...</p>");

    // Initial POST request for the first question
    try {
      const res = await $.ajax({
        url: "http://127.0.0.1:8002/start_interview",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ job: selectedJob })
      });

      if (res && res.text) {
        appendToChat("🤖 AI 面試官", res.text);
      }

      if (res && res.audio_url) {
        $('#tts-audio').attr("src", res.audio_url)[0].play();
      }

    } catch (err) {
      console.error("啟動面試失敗：", err);
      $('#chat-box').html("<p class='text-red-500'>❌ 面試啟動失敗</p>");
      $('#start-interview').prop('disabled', false).text("開始模擬面試");
    }
  });
});

function appendToChat(speaker, message) {
  $('#chat-box').append(`
    <div>
      <span class="font-semibold">${speaker}：</span>
      <span>${message}</span>
    </div>
  `).scrollTop($('#chat-box')[0].scrollHeight);
}
