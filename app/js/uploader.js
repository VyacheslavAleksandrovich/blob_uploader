
function send_part(part_num, part_size, step_size, step, file, threads_stop_array, task_id, parts_upload_array) {
  if(step >= part_num){
    console.log("upload thread №" + (step % step_size) + " done");
    threads_stop_array[step % step_size] = true;
  }
  else{
    console.log("part num: " + part_num + " step_size: " + step_size + " step: " + step + ".");
    var sender = new XMLHttpRequest();
    sender.open("GET", "/upload_url");
    sender.send();
    sender.onload = function () {
      if(this.status != 200){
        console.log("error url get. status: " + this.status);
      }
      else{
        var reader = new FileReader();
        var url = JSON.parse(this.responseText).UploadURL;
        reader.readAsArrayBuffer(file.slice(step*part_size, (step + 1)*part_size));
        reader.onloadend = function () {
          var form = new FormData();
          form.append("file", new Blob([this.result]));
          form.append("file_name", file.name);
          form.append("part_num", step);
          form.append("task_id", task_id);
          var sender = new XMLHttpRequest();
          //sender.addEventListener("progress", function (oEvent) {
          //  console.log("progress");
          //  console.log(oEvent);
          //  if (oEvent.lengthComputable) {
          //    parts_upload_array[step] = oEvent.loaded / oEvent.total;
          //    console.log("step: " + step + " load: " + (oEvent.loaded / oEvent.total));
          //  }
          //});
          sender.upload.onprogress = function(pe) {
            if (pe.lengthComputable) {
              parts_upload_array[step] = pe.loaded / pe.total;
            }
          };
          sender.open("POST", url);
          sender.onload = function () {
            if(this.status != 200){
              console.log("error file part upload. status: " + this.status);
            }
            else{
              parts_upload_array[step] = 1;
              send_part(part_num, part_size, step_size, step + step_size, file, threads_stop_array, task_id, parts_upload_array);
            }
          };
          sender.send(form);
        };
      }
    };
  }
}

function makeid() {
  var text = "";
  var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

  for (var i = 0; i < 128; i++)
    text += possible.charAt(Math.floor(Math.random() * possible.length));

  return text;
}

function get_download_url(task_id, stage) {
  var sender = new XMLHttpRequest();
  sender.open("GET", "/download_url/" + task_id);
  sender.send();
  sender.onload = function () {
    if(this.status != 200){
      console.log("download url query fail status: " + this.status);
    }
    else{
      var DownloadURL = JSON.parse(this.responseText).DownloadURL;
      stage.href = DownloadURL;
      console.log("download_url: " + DownloadURL);
    }
  }
}

function wait_end_merge(task_id, stage) {
  var sender = new XMLHttpRequest();
  sender.open("GET", "/merge_is_done/" + task_id);
  sender.send();
  sender.onload = function () {
    if(this.status != 200){
      console.log("merge is done query fail status: " + this.status);
    }
    else{
      var isDone = JSON.parse(this.responseText).isDone;
      console.log("is done: " + isDone);
      if(isDone) {
        console.log("merge done.");
        get_download_url(task_id, stage);
        stage.text = "Done";
      }
      else{
        console.log("wait");
        setTimeout(function() {wait_end_merge(task_id, stage)}, 2000);
      }
    }
  }
}

function merge_parts(threads_stop_array, file_name, parts, task_id, stage) {
  var is_end = threads_stop_array.every(function (element, index, array) {
    return element;
  });
  if (!is_end) setTimeout(merge_parts, 2000, threads_stop_array, file_name, parts, task_id, stage);
  else{
    console.log("all thereads stop");
    var sender = new XMLHttpRequest();
    sender.open("POST", "/merge_file");
    var form = new FormData();
    form.append("file_name", file_name);
    form.append("number_batches", parts);
    form.append("task_id", task_id);
    sender.send(form);
    sender.onload = function () {
      if(this.status != 200){
        console.log("error merge file. status: " + this.status);
      }
      else{
        console.log("merge task runing, task_id: " + task_id);
        //merge begin, wait_end
        wait_end_merge(task_id, stage);
      };
    }
  }
}

function show_progress(parts_upload_array, parts, progress_bar, stage) {
  var progress = parts_upload_array.reduce(function (a, b) {return a+b;}, 0) / parts * 1;
  progress_bar.value = progress;
  if (progress < 1) setTimeout(show_progress, 1000, parts_upload_array, parts, progress_bar, stage);
  else stage.text = "Merging";
}

function handleSubmit(e) {
  const part_size = 1024*1024*256 ; //256MB
  const nthreads = 2;
  const threads_stop_array = []; //для отслеживания завершившихся потоков
  const parts_upload_array = []; //для отслеживания завершённых загрузок
  var progress_bar = document.getElementById("progress-bar");
  var stage = document.getElementById("stage");
  progress_bar.value = 0;
  stage.text = "Upload";
  stage.href = "#";
  e.preventDefault();
  if(this.file.files[0] === undefined) return false;
  var file_ = this.file.files[0];
  const parts = Math.ceil(file_.size / part_size);
  for(var i=0; i < nthreads; i++) {
    if (i < parts) threads_stop_array[i] = false;
    else threads_stop_array[i] = true;
  }
  for(var i=0; i < parts; i++){
    parts_upload_array[i] = 0;
  }
  var task_id = makeid();
  for(var i=0; i < nthreads; i++){
    if (i < parts) send_part(parts, part_size, nthreads, i, file_, threads_stop_array, task_id, parts_upload_array);
  }
  show_progress(parts_upload_array, parts, progress_bar, stage);
  merge_parts(threads_stop_array, file_.name, parts, task_id, stage);
  return false;
}
