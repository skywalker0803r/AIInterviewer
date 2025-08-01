$(document).ready(function () {
  $('#fetch-jobs').click(function () {
    $.get('http://127.0.0.1:8001/jobs?keyword=前端工程師')
      .done(function (data) {
        console.log("成功接收到資料：", data);
        $('#job-list').empty();
        if (data.jobs.length === 0) {
          $('#job-list').append(`<li class="text-gray-500">查無職缺</li>`);
          return;
        }

        data.jobs.forEach(job => {
          $('#job-list').append(`
            <li class="border p-3 rounded hover:bg-gray-50">
              <a href="${job.url}" target="_blank" class="text-blue-600 font-semibold">${job.title}</a>
              <div class="text-sm text-gray-600">${job.company}</div>
            </li>
          `);
        });
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        console.error("發生錯誤：", textStatus, errorThrown);
        $('#job-list').append(`<li class="text-red-500">後端錯誤，請稍後再試</li>`);
      });
  });
});
