var SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
const recognition = new SpeechRecognition();


function searchFromVoice() {
    recognition.start();

    recognition.onresult = (event) => {
        const speechToText = event.results[0][0].transcript;
        console.log(speechToText);

        document.getElementById("searchbar").value = speechToText;
        search();
    }
}

function search() {
    var searchTerm = document.getElementById("searchbar").value;
    var apigClient = apigClientFactory.newClient();

    var params = {
        q: searchTerm
    };
    var body = {
        "q": searchTerm
    };

    var additionalParams = {
        queryParams: {
            q: searchTerm
        }
    };
    apigClient.searchGet(params, body, additionalParams)
        .then(function(result) {
            console.log('OK');
            console.log(result)
            showImages(result.data);
            document.getElementById("searchbar").value = ""
        }).catch(function(result) {
            console.log("Not OK");
        });
}


function showImages(res) {
    var newDiv = document.getElementById("images");
    if (typeof(newDiv) != 'undefined' && newDiv != null) {
        while (newDiv.firstChild) {
            newDiv.removeChild(newDiv.firstChild);
        }
    }

    console.log("Result in showImages",res);
    if (res.length == 0) {
        var newContent = document.createTextNode("No image to display");
        newDiv.appendChild(newContent);
    } else {
        for (var i = 0; i < res.length; i++) {
            console.log(res[i]);
            var newDiv = document.getElementById("images");
            var newimg = document.createElement("img");
            newimg.classList.add('col-md-3');
            newimg.classList.add('img-fluid');
            newimg.src = res[i].url;
            newDiv.append(newimg);
        }
    }


    // console.log(res.Responses.length);
    // if (res.Responses.length == 0) {
    //     var newContent = document.createTextNode("No image to display");
    //     newDiv.appendChild(newContent);
    // } else {
    //     for (var i = 0; i < res.Responses.length; i++) {
    //         console.log(res.Responses[i]);
    //         var newDiv = document.getElementById("images");
    //         var newimg = document.createElement("img");
    //         newimg.src = res.Responses[i].url;
    //         newDiv.appendChild(newimg);
    //     }
    // }
}

const realFileBtn = document.getElementById("realfile");

function upload() {
    realFileBtn.click();
}

function previewFile(input) {

    var reader = new FileReader();
    var name = input.files[0].name;
    var type = input.files[0].type;
    var customLabels = document.getElementById("searchbar").value;

    console.log(name);
    console.log(type);
    fileExt = name.split(".").pop();
    var onlyname = name.replace(/\.[^/.]+$/, "");
    var finalName = onlyname + "_" + Date.now() + "." + fileExt;
    name = finalName;

    reader.onload = function(e) {
        var src = e.target.result;

        var newImage = document.createElement("img");
        newImage.src = src;
        encoded = newImage.outerHTML;
        // console.log(encoded);
        // showImages(input.files[0]);
        last_index_quote = encoded.lastIndexOf('"');
        if (fileExt == 'jpg' || fileExt == 'jpeg' || fileExt == 'png') {
            encodedStr = encoded.substring(33, last_index_quote);
        } else {
            encodedStr = encoded.substring(32, last_index_quote);
        }
        var apigClient = apigClientFactory.newClient();

        var params = {
            "item": name,
            "folder": "photos-2402",
            "Content-Type": type + ";base64",
            "x-amz-meta-customLabels": customLabels,
        };

        var additionalParams = {
            headers: {
                "Content-Type": type + ";base64",
                "x-amz-meta-customLabels": customLabels
            }
        };
        // console.log(encodedStr);

        // refer to https://stackoverflow.com/questions/65346277/createobjecturl-overload-resolution-failed
        // var blobObj = new Blob([atob(encodedStr)], { type: "image/jpg" });
        // console.log(blobObj);
        // console.log(encodedStr);

        console.log("start making PUT ...")
        apigClient.uploadFolderItemPut(params, encodedStr, additionalParams)
            .then(function(result) {
                console.log('PUT alert: success OK');
                document.getElementById("success_msg").innerHTML = "Successfully Uploaded"
                document.getElementById("searchbar").value = ""
            }).catch(function(result) {
                console.log("catch PUT result: ",result);
            });
    }

    reader.readAsDataURL(input.files[0]);
}

// window.URL = window.URL || window.webkitURL;

// function importFileandPreview() {
//   var preview = document.querySelector('img');
//   var file    = document.querySelector('input[type=file]').files[0];

//   preview.src = window.URL.createObjectURL(file);
//   preview.onload = function() {
//     window.URL.revokeObjectURL(this.src);
//   }
  
//   document.getElementById("srcAttribute").innerHTML = "<b>src attribute:</b> " + preview.src;  
// }