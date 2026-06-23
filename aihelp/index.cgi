#!/usr/bin/perl
# index.cgi
# Main page of the AI Help Chatbot module

use strict;
use warnings;
require '../web-lib.pl';
require './aihelp-lib.pl';
our (%text, %config, %in, $module_name);

&init_config();
&ReadParse();
my %cfg = &get_config();

# Print HTML Header
&ui_print_header(undef, $text{'index_title'}, "");

if (!$cfg{'gemini_api_key'} || $in{'mode'} eq 'settings') {
    # Render API Key and Google OAuth configuration form
    print &ui_form_start("save_config.cgi", "post");
    
    # 1. Gemini Settings
    print &ui_table_start("Gemini AI API Settings", undef, 2);
    
    print &ui_table_row($text{'index_apikey'},
                        &ui_textbox("gemini_api_key", $cfg{'gemini_api_key'}, 60, 0, 100, "placeholder=\"AIzaSy...\""));
    
    print &ui_table_row("", $text{'index_apikey_desc'});
    
    print &ui_table_end();
    
    # 2. Google OAuth Settings
    print &ui_table_start("Google OAuth2 Authentication Settings", undef, 2);
    
    print &ui_table_row("Enable Google Login",
                        &ui_yesno_radio("google_auth_enabled", $cfg{'google_auth_enabled'} || 0, 1, 0));
    
    print &ui_table_row("Google Client ID",
                        &ui_textbox("google_client_id", $cfg{'google_client_id'}, 60, 0, 200, "placeholder=\"...apps.googleusercontent.com\""));
    
    print &ui_table_row("Google Client Secret",
                        &ui_password("google_client_secret", $cfg{'google_client_secret'}, 60, 0, 200));
                        
    print &ui_table_row("Allowed Email Domains",
                        &ui_textbox("google_allowed_domains", $cfg{'google_allowed_domains'}, 60, 0, 200, "placeholder=\"armellini.com\""));
                        
    print &ui_table_row("Default Webmin User mapping",
                        &ui_textbox("google_default_user", $cfg{'google_default_user'} || "admin", 20, 0, 50));
    
    print &ui_table_row("", "Configure your Google Cloud Project (e.g. <code>teamsmschat</code>) credentials. Make sure to add <code>https://&lt;your-server&gt;:10000/unauthenticated/google_oauth.cgi</code> to your authorized redirect URIs in the Google Developer Console.");
    
    print &ui_table_end();
    
    my @buttons = ( [ "save", $text{'index_save'} ] );
    if ($cfg{'gemini_api_key'}) {
        push(@buttons, [ "cancel", "Back to Chat", undef, undef, "onClick=\"window.location='index.cgi'; return false;\"" ]);
    }
    print &ui_form_end(\@buttons);
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
        height: 620px;
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
    
    /* Avatars and Message Rows */
    .chat-message-row {
        display: flex;
        gap: 12px;
        max-width: 80%;
        align-items: flex-start;
        animation: bubble-fade 0.3s ease;
    }
    .chat-message-row.user {
        align-self: flex-end;
        flex-direction: row-reverse;
    }
    .chat-message-row.bot {
        align-self: flex-start;
    }
    .chat-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
    }
    .chat-avatar.user {
        background: #312e81;
        color: white;
    }
    .chat-avatar.bot {
        background: #7c3aed;
        color: white;
    }
    
    .chat-bubble {
        max-width: 100%;
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 14px;
        line-height: 1.5;
    }
    \@keyframes bubble-fade {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .chat-bubble.bot {
        background: white;
        border: 1px solid #e2e8f0;
        color: #1e293b;
        border-top-left-radius: 4px;
    }
    .chat-bubble.user {
        background: #1e293b;
        color: white;
        border-top-right-radius: 4px;
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
    
    /* Pill shape input and attachments */
    .ai-chatbot-input-wrapper {
        flex: 1;
        display: flex;
        align-items: center;
        border: 1px solid #cbd5e1;
        border-radius: 24px;
        padding: 4px 16px;
        background: white;
        transition: border-color 0.2s ease;
    }
    .ai-chatbot-input-wrapper:focus-within {
        border-color: #4f46e5;
    }
    .ai-chatbot-input-wrapper i.input-icon {
        color: #94a3b8;
        font-size: 16px;
        margin-right: 8px;
    }
    .ai-chatbot-input {
        flex: 1;
        border: none;
        padding: 8px 0;
        font-size: 14px;
        outline: none;
        background: transparent;
    }
    .ai-chatbot-send-btn {
        width: 40px;
        height: 40px;
        background: #4f46e5;
        color: white;
        border: none;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: background 0.2s ease;
        flex-shrink: 0;
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
        <h3><i class="fa fa-android"></i> AEL-WebMin AI Assistant</h3>
        <div class="actions">
            <a href="#" id="clear-chat-btn"><i class="fa fa-trash"></i> $text{'index_clear'}</a>
            <a href="index.cgi?mode=settings"><i class="fa fa-cog"></i> $text{'index_settings'}</a>
        </div>
    </div>
    
    <div class="ai-chatbot-messages" id="chat-messages">
        <div class="chat-message-row bot">
            <div class="chat-avatar bot"><i class="fa fa-android"></i></div>
            <div class="chat-bubble bot">
                <p>$text{'index_bot_welcome'}</p>
            </div>
        </div>
    </div>
    
    <div class="ai-chatbot-input-area">
        <div class="ai-chatbot-input-wrapper">
            <i class="fa fa-paperclip input-icon"></i>
            <input type="text" class="ai-chatbot-input" id="chat-input" placeholder="$text{'index_prompt_placeholder'}" autocomplete="off">
        </div>
        <button class="ai-chatbot-send-btn" id="send-btn"><i class="fa fa-arrow-right"></i></button>
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
            <div class="chat-message-row bot">
                <div class="chat-avatar bot"><i class="fa fa-android"></i></div>
                <div class="chat-bubble bot">
                    <p>$text{'index_bot_welcome'}</p>
                </div>
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
        const row = document.createElement("div");
        row.className = "chat-message-row " + sender;
        
        const avatar = document.createElement("div");
        avatar.className = "chat-avatar " + sender;
        if (sender === "bot") {
            avatar.innerHTML = '<i class="fa fa-android"></i>';
        } else {
            avatar.innerHTML = '<i class="fa fa-user"></i>';
        }
        
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble " + sender;
        if (sender === "bot") {
            bubble.innerHTML = parseMarkdown(text);
        } else {
            bubble.textContent = text;
        }
        
        row.appendChild(avatar);
        row.appendChild(bubble);
        chatMessages.appendChild(row);
        scrollToBottom();
    }
    
    function showTypingIndicator() {
        const row = document.createElement("div");
        row.className = "chat-message-row bot";
        row.id = "typing-indicator-row";
        
        const avatar = document.createElement("div");
        avatar.className = "chat-avatar bot";
        avatar.innerHTML = '<i class="fa fa-android"></i>';
        
        const bubble = document.createElement("div");
        bubble.className = "chat-bubble bot";
        bubble.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        row.appendChild(avatar);
        row.appendChild(bubble);
        chatMessages.appendChild(row);
        scrollToBottom();
    }
    
    function removeTypingIndicator() {
        const indicator = document.getElementById("typing-indicator-row");
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
