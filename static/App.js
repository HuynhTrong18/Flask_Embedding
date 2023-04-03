class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button')
        }

        this.state = false;
        this.chats = [];
    }

    display() {
        const {openButton, chatBox, sendButton} = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox))

        sendButton.addEventListener('click', () => this.onSendButton(chatBox))

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({key}) => {
            if (key === "Enter") {
                this.onSendButton(chatBox)
            }
        })
    }

    toggleState(chatbox) {
        this.state = !this.state;
        // show or hides the box
        if(this.state) {
            chatbox.classList.add('chatbox--active')
            if (this.chats.length == 0) {
                let hi = { role: "assistant", content: 'Xin chào, tôi là nhân viên hỗ trợ bán hàng của Gear VN. Bạn có thể cho tôi biết bạn đang quan tâm đến sản phẩm nào của chúng tôi không ạ?' };
                this.chats.push(hi);
                this.updateChatText(chatbox)
            }
        } else {
            chatbox.classList.remove('chatbox--active')
        }
    
    }

    onSendButton(chatbox) {
        var textField = chatbox.querySelector('input');
        let question = textField.value;
        textField.value = ''
        if(question == ""){
            return;
        }
        
        let msg = { role: "user", content: question }
        this.chats.push(msg);
        
        let say_hi =  ["hi","xin chào","hello","chào","hi!","xin chào!","hello!","chào!"]
        if (say_hi.includes(question.toLowerCase())) {
            let hi = { role: "assistant", content: 'Xin chào, tôi là nhân viên hỗ trợ bán hàng của Gear VN. Bạn có thể cho tôi biết bạn đang quan tâm đến sản phẩm nào của chúng tôi không ạ?' };
            this.chats.push(hi);
            this.updateChatText(chatbox)
            return;
        }

        msg = { role: "assistant", content: "..." }
        this.chats.push(msg);

        this.updateChatText(chatbox)
        
        var hosting = "https://ht-chatbot-openai.azurewebsites.net"
        fetch(hosting + '/api-backend/chats', {
            method: 'POST',
            body: JSON.stringify({ chats: this.chats}),
            mode: 'cors',
            headers: {
              'Content-Type': 'application/json'
            },
          })
          .then(r => r.json())
          .then(r => {
            this.chats.pop(msg);
            msg = { role: "assistant", content: r.answer };
            this.chats.push(msg);
            this.updateChatText(chatbox)

        }).catch((error) => {
            console.error('Error:', error);
            this.chats.pop(msg);
            msg = { role: "assistant", content: "Hệ thông tạm không có phản hồi. Vui lòng thử lại sau ít phút" };
            this.chats.push(msg);
            this.updateChatText(chatbox)
        });
    }
    
    updateChatText(chatbox) {
        var html = '';
        this.chats.slice().reverse().forEach(function(item, index) {
            if (item.role === "assistant")
            {
                if(item.content == "..."){
                    html += "<div class='messages__item typing'><span></span><span></span><span></span></div>"
                }
                else {
                    html += '<div class="messages__item messages__item--visitor">' + replaceURLs(item.content) + '</div>'
                }
            }
            else
            {
                html += '<div class="messages__item messages__item--operator">' +  replaceURLs(item.content) + '</div>'
            }
          });

        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
    }
}


const chatbox = new Chatbox();
chatbox.display();

function replaceURLs(message) {
    if(!message) return;
   
    var urlRegex = /(((https?:\/\/)|(www\.))[^\s]+)/g;
    return message.replace(urlRegex, function (url) {
      var hyperlink = url;
      if (!hyperlink.match('^https?:\/\/')) {
        hyperlink = 'http://' + hyperlink;
      }
      return '<a href="' + hyperlink + '" target="_blank" rel="noopener noreferrer">'+ hyperlink +'</a>'
    });
  }