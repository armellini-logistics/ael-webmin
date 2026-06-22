#!/usr/bin/perl
# index.cgi
# Main page of the AI Help Chatbot module

use strict;
use warnings;
require '../web-lib.pl';
require './aihelp-lib.pl';
our (%text, %config, $module_name);

&init_config();
my %cfg = &get_config();

# Print HTML Header
&ui_print_header(undef, $text{'index_title'}, "");

if (!$cfg{'gemini_api_key'}) {
    # Render API Key configuration form
    print &ui_form_start("save_config.cgi", "post");
    print &ui_table_start($text{'index_apikey'}, undef, 2);
    
    print &ui_table_row($text{'index_apikey'},
                        &ui_textbox("gemini_api_key", undef, 60, 0, 100, "placeholder=\"AIzaSy...\""));
    
    print &ui_table_row("", $text{'index_apikey_desc'});
    
    print &ui_table_end();
    print &ui_form_end([ [ "save", $text{'index_save'} ] ]);
}
else {
    # Render Chatbot Interface
    # Embed a style block for high visual aesthetics
    print <<EOF;
<style>
    .ai-chatbot-container {
        max-width: 900px;
        margin: 20px auto;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
        backdrop-filter: blur(12px);
        display: flex;
        flex-direction: column;
        height: 600px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        overflow: hidden;
    }
    .ai-chatbot-header {
        padding: 16px 24px;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top-left-radius: 15px;
        border-top-right-radius: 15px;
    }
    .ai-chatbot-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        color: white;
    }
    .ai-chatbot-header .actions {
        display: flex;
        gap: 10px;
    }
    .ai-chatbot-header .actions a {
        color: rgba(255, 255, 255, 0.9);
        background: rgba(255, 255, 255, 0.2);
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 12px;
        text-decoration: none;
        transition: all 0.2s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .ai-chatbot-header .actions a:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: translateY(-1px);
    }
    .ai-chatbot-messages {
        flex: 1;
        padding: 24px;
        overflow-y: auto;
        background: #f8fafc;
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .chat-bubble {
        max-width: 75%;
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 14px;
        line-height: 1.5;
        animation: bubble-fade 0.3s ease;
    }
    \@keyframes bubble-fade {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .chat-bubble.bot {
        align-self: flex-start;
        background: white;
        border: 1px solid #e2e8f0;
        color: #1e293b;
        border-bottom-left-radius: 4px;
    }
    .chat-bubble.user {
        align-self: flex-end;
        background: #4f46e5;
        color: white;
        border-bottom-right-radius: 4px;
    }
    .chat-bubble p {
        margin: 0 0 10px 0;
    }
    .chat-bubble p:last-child {
        margin-bottom: 0;
    }
    .chat-bubble code {
        background: rgba(0, 0, 0, 0.05);
        padding: 2px 4px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 13px;
    }
    .chat-bubble.user code {
        background: rgba(255, 255, 255, 0.2);
    }
    .chat-bubble pre {
        background: #0f172a;
        color: #f8fafc;
        padding: 12px;
        border-radius: 8px;
        overflow-x: auto;
        margin: 10px 0;
    }
    .chat-bubble pre code {
        background: transparent;
        color: inherit;
        padding: 0;
    }
    .ai-chatbot-input-area {
        padding: 16px 24px;
        background: white;
        border-top: 1px solid #e2e8f0;
        display: flex;
        gap: 12px;
        align-items: center;
    }
    .ai-chatbot-input {
        flex: 1;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 14px;
        outline: none;
        transition: border-color 0.2s ease;
    }
    .ai-chatbot-input:focus {
        border-color: #4f46e5;
    }
    .ai-chatbot-send-btn {
        background: #4f46e5;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 20px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s ease;
    }
    .ai-chatbot-send-btn:hover {
        background: #3730a3;
    }
    .typing-indicator {
        display: flex;
        gap: 4px;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 20px;
    }
    .typing-dot {
        width: 6px;
        height: 6px;
        background: #94a3b8;
        border-radius: 50%;
        animation: typing-bounce 1s infinite ease-in-out;
    }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    \@keyframes typing-bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }
</style>

<div class="ai-chatbot-container">
    <div class="ai-chatbot-header">
        <h3><i class="fa fa-android"></i> Webmin AI Assistant</h3>
        <div class="actions">
            <a href="#" id="clear-chat-btn"><i class="fa fa-trash"></i> $text{'index_clear'}</a>
            <a href="save_config.cgi?clear_key=1"><i class="fa fa-cog"></i> $text{'index_settings'}</a>
        </div>
    </div>
    
    <div class="ai-chatbot-messages" id="chat-messages">
        <div class="chat-bubble bot">
            <p>$text{'index_bot_welcome'}</p>
        </div>
    </div>
    
    <div class="ai-chatbot-input-area">
        <input type="text" class="ai-chatbot-input" id="chat-input" placeholder="$text{'index_prompt_placeholder'}" autocomplete="off">
        <button class="ai-chatbot-send-btn" id="send-btn">$text{'index_send'} <i class="fa fa-paper-plane"></i></button>
    </div>
</div>

<script>
document.addEventListener("DOMContentLoaded", function() {
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const clearBtn = document.getElementById("clear-chat-btn");
    
    // Auto-scroll messages container
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Clear chat history
    clearBtn.addEventListener("click", function(e) {
        e.preventDefault();
        chatMessages.innerHTML = `
            <div class="chat-bubble bot">
                <p>$text{'index_bot_welcome'}</p>
            </div>
        `;
        scrollToBottom();
    });
    
    // Simple markdown to HTML parser for standard code block rendering
    function parseMarkdown(text) {
        let html = text;
        // Escape HTML tags to prevent XSS
        html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        
        // Code blocks
        html = html.replace(/\\`\\`\\`(\\w*)\\n([\\s\\S]*?)\\`\\`\\`/g, function(match, lang, code) {
            return '<pre><code>' + code.trim() + '</code></pre>';
        });
        
        // Inline code
        html = html.replace(/\\`([^`]+)\\`/g, '<code>\$1</code>');
        
        // Bold
        html = html.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>\$1</strong>');
        
        // Paragraphs / Linebreaks
        html = html.split('\\n\\n').map(p => {
            if (p.trim().startsWith('<pre>')) return p;
            return '<p>' + p.trim().replace(/\\n/g, '<br>') + '</p>';
        }).join('');
        
        return html;
    }
    
    function appendMessage(sender, text) {
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble " + sender;
        if (sender === "bot") {
            bubble.innerHTML = parseMarkdown(text);
        } else {
            bubble.textContent = text;
        }
        chatMessages.appendChild(bubble);
        scrollToBottom();
    }
    
    function showTypingIndicator() {
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble bot";
        bubble.id = "typing-indicator-bubble";
        bubble.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatMessages.appendChild(bubble);
        scrollToBottom();
    }
    
    function removeTypingIndicator() {
        const indicator = document.getElementById("typing-indicator-bubble");
        if (indicator) {
            indicator.remove();
        }
    }
    
    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Append user message
        appendMessage("user", message);
        chatInput.value = "";
        
        // Show typing indicator
        showTypingIndicator();
        
        // Perform AJAX request to chat.cgi
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "chat.cgi", true);
        xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                removeTypingIndicator();
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.reply) {
                            appendMessage("bot", response.reply);
                        } else if (response.error) {
                            appendMessage("bot", "Error: " + response.error);
                        } else {
                            appendMessage("bot", "Error: Could not retrieve response.");
                        }
                    } catch (e) {
                        appendMessage("bot", "Error: Failed to parse server response.");
                    }
                } else {
                    removeTypingIndicator();
                    appendMessage("bot", "Error: Failed to contact helper endpoint.");
                }
            }
        };
        xhr.send("message=" + encodeURIComponent(message));
    }
    
    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
});
</script>
EOF
}

# Print HTML Footer
&ui_print_footer("/", $text{'index_return'});
