function send_part(part_num, part_size, step_size, step, file, result_array, task_id) {
  if(step >= part_num){
    console.log("upload step: " + step + " done");
    console.log("upload thread №" + (step % step_size) + " done");
    result_array[step % step_size] = true;
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
          var sender = new XMLHttpRequest();
          sender.open("POST", url);
          var form = new FormData();
          form.append("file", new Blob([this.result]));
          form.append("file_name", file.name);
          form.append("part_num", step);
          form.append("task_id", task_id);
          sender.send(form);
          sender.onload = function () {
            if(this.status != 200){
              console.log("error file part upload. status: " + this.status);
            }
            else{
              send_part(part_num, part_size, step_size, step + step_size, file, result_array, task_id);
            }
          };
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

function get_download_url(task_id) {
  var sender = new XMLHttpRequest();
  sender.open("GET", "/download_url/" + task_id);
  sender.send();
  sender.onload = function () {
    if(this.status != 200){
      console.log("download url query fail status: " + this.status);
    }
    else{
      var DownloadURL = JSON.parse(this.responseText).DownloadURL;
      console.log("download_url: " + DownloadURL);
    }
  }
}

function wait_end_merge(task_id) {
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
        get_download_url(task_id);
      }
      else{
        console.log("wait");
        setTimeout(function() {wait_end_merge(task_id)}, 1000);
      }
    }
  }
}

function merge_parts(result_array, file_name, parts, task_id) {
  var is_end = result_array.every(function (element, index, array) {
    return element;
  });
  if (!is_end) setTimeout(merge_parts, 1000, result_array, file_name, parts, task_id);
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
        wait_end_merge(task_id);
      };
    }
  }
}

function handleSubmit(e) {
  const part_size = 1024*1024*256; //256MB
  const nthreads = 2;
  const result_array = [];
  e.preventDefault();
  if(this.file.files[0] === undefined) return false;
  var file_ = this.file.files[0];
  const parts = Math.ceil(file_.size / part_size);
  for(var i=0; i < nthreads; i++) {
    result_array[i] = false;
  }
  var task_id = makeid();
  for(var i=0; i < nthreads; i++){
    send_part(parts, part_size, nthreads, i, file_, result_array, task_id);
  }
  merge_parts(result_array, file_.name, parts, task_id);
  return false;
}
