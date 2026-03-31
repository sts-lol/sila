// Configuration
const API_URL = 'api.php';

// State
let allConversations = [];
let currentFilter = 'all';
let currentAssistantFilter = 'all';
let currentTopicFilter = null; // null means no topic filter

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadDashboard();
    });

    document.getElementById('statusFilter').addEventListener('change', (e) => {
        currentFilter = e.target.value;
        displayConversations(allConversations);
    });

    document.getElementById('assistantFilter').addEventListener('change', (e) => {
        currentAssistantFilter = e.target.value;
        loadStatistics();
        loadLinguistics();
        loadWordCloud();
        loadCooccurrence();
    });

    document.getElementById('clearTopicFilterBtn').addEventListener('click', () => {
        clearTopicFilter();
    });

    // Word cloud controls
    document.getElementById('minWordLength').addEventListener('change', () => {
        loadWordCloud();
        loadCooccurrence();
    });

    document.getElementById('topWordsCount').addEventListener('change', () => {
        loadWordCloud();
        loadCooccurrence();
    });

    document.getElementById('refreshWordCloud').addEventListener('click', () => {
        loadWordCloud();
        loadCooccurrence();
    });

    // Linguistics tabs
    document.querySelectorAll('.ling-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and content
            document.querySelectorAll('.ling-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.ling-tab-content').forEach(c => c.classList.remove('active'));

            // Add active class to clicked tab
            tab.classList.add('active');

            // Show corresponding content
            const tabName = tab.dataset.tab;
            const contentId = 'linguistics' + tabName.charAt(0).toUpperCase() + tabName.slice(1);
            document.getElementById(contentId).classList.add('active');
        });
    });

    // Relationship visualization tabs
    document.querySelectorAll('.rel-viz-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.rel-viz-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.rel-viz-panel').forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const vizType = tab.dataset.viz;
            document.getElementById('viz' + vizType.charAt(0).toUpperCase() + vizType.slice(1)).classList.add('active');
        });
    });

    // Word search functionality
    document.getElementById('wordSearchBtn').addEventListener('click', () => {
        const word = document.getElementById('wordSearchInput').value.trim();
        if (word) {
            searchWordContext(word);
        }
    });

    document.getElementById('wordSearchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const word = e.target.value.trim();
            if (word) {
                searchWordContext(word);
            }
        }
    });

    // Close modal when clicking outside
    document.getElementById('conversationModal').addEventListener('click', (e) => {
        if (e.target.id === 'conversationModal') {
            closeModal();
        }
    });
}

// Load all dashboard data
async function loadDashboard() {
    try {
        await Promise.all([
            loadStatistics(),
            loadConversations(),
            loadWordCloud(),
            loadCooccurrence(),
            loadLinguistics(),
            loadRelationships()
        ]);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const url = currentAssistantFilter === 'all'
            ? `${API_URL}?action=stats`
            : `${API_URL}?action=stats&assistant=${encodeURIComponent(currentAssistantFilter)}`;

        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            const stats = result.data;
            document.getElementById('totalConversations').textContent = stats.total_conversations;
            document.getElementById('completedConversations').textContent = stats.completed_conversations;
            document.getElementById('failedConversations').textContent = stats.failed_conversations;
            document.getElementById('inProgressConversations').textContent = stats.in_progress_conversations;
            document.getElementById('totalMessages').textContent = stats.total_messages;
            document.getElementById('avgConversationLength').textContent = stats.average_conversation_length;
            document.getElementById('totalCharacters').textContent = formatNumber(stats.total_characters);
            document.getElementById('avgMessageLength').textContent = stats.average_message_length;

            // Populate assistant filter dropdown (only on first load or when showing all)
            if (currentAssistantFilter === 'all' && stats.available_assistants) {
                populateAssistantFilter(stats.available_assistants);
            }

            // Display topic statistics
            displayTopicStats(stats);
        } else {
            throw new Error(result.error || 'Failed to load statistics');
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Populate assistant filter dropdown
function populateAssistantFilter(assistants) {
    const filter = document.getElementById('assistantFilter');
    const currentValue = filter.value;

    // Keep "All Assistants" option and add assistants
    filter.innerHTML = '<option value="all">All Assistants</option>';

    assistants.forEach(assistant => {
        const option = document.createElement('option');
        option.value = assistant.slug;
        option.textContent = assistant.name;
        filter.appendChild(option);
    });

    // Restore previous selection if it still exists
    if (currentValue !== 'all') {
        filter.value = currentValue;
    }
}

// Display topic statistics
function displayTopicStats(stats) {
    const topTopicsContainer = document.getElementById('topTopics');
    const topCultureContainer = document.getElementById('topCulture');
    const topFeelingsContainer = document.getElementById('topFeelings');

    // Display top topics
    if (stats.top_topics && stats.top_topics.length > 0) {
        topTopicsContainer.innerHTML = stats.top_topics.map(item =>
            `<div class="topic-item clickable" data-topic="${escapeHtml(item.name)}" data-type="topic">
                <span class="topic-name">${escapeHtml(item.name)}</span>
                <span class="topic-count">${item.count}</span>
            </div>`
        ).join('');

        // Add click listeners to topics
        topTopicsContainer.querySelectorAll('.topic-item').forEach(item => {
            item.addEventListener('click', () => {
                const topic = item.dataset.topic;
                const type = item.dataset.type;
                filterByTopic(topic, type);
            });
        });
    } else {
        topTopicsContainer.innerHTML = '<p class="loading">No data available</p>';
    }

    // Display top cultural references
    if (stats.top_cultural_references && stats.top_cultural_references.length > 0) {
        topCultureContainer.innerHTML = stats.top_cultural_references.map(item =>
            `<div class="topic-item clickable" data-topic="${escapeHtml(item.name)}" data-type="cultural_reference">
                <span class="topic-name">${escapeHtml(item.name)}</span>
                <span class="topic-count">${item.count}</span>
            </div>`
        ).join('');

        // Add click listeners to cultural references
        topCultureContainer.querySelectorAll('.topic-item').forEach(item => {
            item.addEventListener('click', () => {
                const topic = item.dataset.topic;
                const type = item.dataset.type;
                filterByTopic(topic, type);
            });
        });
    } else {
        topCultureContainer.innerHTML = '<p class="loading">No data available</p>';
    }

    // Display top feeling types
    if (stats.top_feeling_types && stats.top_feeling_types.length > 0) {
        topFeelingsContainer.innerHTML = stats.top_feeling_types.map(item =>
            `<div class="topic-item clickable" data-topic="${escapeHtml(item.name)}" data-type="feeling_type">
                <span class="topic-name">${escapeHtml(item.name)}</span>
                <span class="topic-count">${item.count}</span>
            </div>`
        ).join('');

        // Add click listeners to feeling types
        topFeelingsContainer.querySelectorAll('.topic-item').forEach(item => {
            item.addEventListener('click', () => {
                const topic = item.dataset.topic;
                const type = item.dataset.type;
                filterByTopic(topic, type);
            });
        });
    } else {
        topFeelingsContainer.innerHTML = '<p class="loading">No data available</p>';
    }
}

// Filter conversations by topic
function filterByTopic(topic, type) {
    currentTopicFilter = { topic, type };

    // Update UI to show filter is active
    const clearBtn = document.getElementById('clearTopicFilterBtn');
    const filterInfo = document.getElementById('topicFilterInfo');

    clearBtn.style.display = 'block';
    filterInfo.style.display = 'block';

    const typeLabel = type === 'topic' ? 'Topic' :
                      type === 'cultural_reference' ? 'Cultural Reference' :
                      'Feeling Type';
    filterInfo.textContent = `Filtering by ${typeLabel}: "${topic}"`;

    // Scroll to conversations section
    document.querySelector('.conversations-section').scrollIntoView({ behavior: 'smooth' });

    // Load and filter conversations
    loadAndFilterConversations();
}

// Clear topic filter
function clearTopicFilter() {
    currentTopicFilter = null;

    // Update UI
    document.getElementById('clearTopicFilterBtn').style.display = 'none';
    document.getElementById('topicFilterInfo').style.display = 'none';

    // Reload conversations without topic filter
    displayConversations(allConversations);
}

// Load conversations and apply topic filter
async function loadAndFilterConversations() {
    const container = document.getElementById('conversationsList');
    container.innerHTML = '<p class="loading">Loading conversations...</p>';

    try {
        // Fetch all conversation details with their original filenames
        const conversationDetailsWithFilenames = await Promise.all(
            allConversations.map(async (conv) => {
                const response = await fetch(`${API_URL}?action=get&file=${encodeURIComponent(conv.filename)}`);
                const result = await response.json();
                return result.success ? { data: result.data, filename: conv.filename } : null;
            })
        );

        // Filter conversations that contain the selected topic
        const filtered = conversationDetailsWithFilenames.filter(item => {
            if (!item || !item.data) return false;

            const conv = item.data;
            const { topic, type } = currentTopicFilter;

            // Check if any message in the conversation contains the topic
            return conv.messages.some(msg => {
                if (!msg.analysis) return false;

                if (type === 'topic') {
                    return msg.analysis.topics && msg.analysis.topics.includes(topic);
                } else if (type === 'cultural_reference') {
                    return msg.analysis.cultural_references && msg.analysis.cultural_references.includes(topic);
                } else if (type === 'feeling_type') {
                    return msg.analysis.feeling_types && msg.analysis.feeling_types.includes(topic);
                }

                return false;
            });
        });

        if (filtered.length === 0) {
            container.innerHTML = '<p class="loading">No conversations found with this topic</p>';
            return;
        }

        // Convert back to conversation list format for display, preserving original filenames
        const conversationsToDisplay = filtered.map(item => {
            const conv = item.data;
            return {
                filename: item.filename, // Use the original filename
                id: conv.id,
                timestamp: conv.timestamp,
                status: conv.status,
                total_messages: conv.total_messages,
                completed_messages: conv.messages.length,
                assistant_1_id: conv.assistant_1_id,
                assistant_1_name: conv.assistant_1_name,
                assistant_1_slug: conv.assistant_1_slug,
                assistant_2_id: conv.assistant_2_id,
                assistant_2_name: conv.assistant_2_name,
                assistant_2_slug: conv.assistant_2_slug
            };
        });

        displayConversations(conversationsToDisplay);
    } catch (error) {
        console.error('Error filtering conversations:', error);
        container.innerHTML = '<p class="error">Failed to filter conversations</p>';
    }
}

// Load conversations list
async function loadConversations() {
    const container = document.getElementById('conversationsList');
    container.innerHTML = '<p class="loading">Loading conversations...</p>';

    try {
        const response = await fetch(`${API_URL}?action=list`);
        const result = await response.json();

        if (result.success) {
            allConversations = result.data;
            displayConversations(allConversations);
        } else {
            throw new Error(result.error || 'Failed to load conversations');
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
        container.innerHTML = '<p class="error">Failed to load conversations</p>';
    }
}

// Display conversations with filtering
function displayConversations(conversations) {
    const container = document.getElementById('conversationsList');

    // Filter conversations
    let filtered = conversations;
    if (currentFilter !== 'all') {
        filtered = conversations.filter(conv => conv.status === currentFilter);
    }

    if (filtered.length === 0) {
        container.innerHTML = '<p class="loading">No conversations found</p>';
        return;
    }

    container.innerHTML = filtered.map(conv => createConversationCard(conv)).join('');

    // Add click listeners
    document.querySelectorAll('.conversation-card').forEach(card => {
        card.addEventListener('click', () => {
            const filename = card.dataset.filename;
            loadConversationDetails(filename);
        });
    });
}

// Create conversation card HTML
function createConversationCard(conversation) {
    const statusClass = `status-${conversation.status}`;
    const completionPercentage = Math.round((conversation.completed_messages / conversation.total_messages) * 100);

    return `
        <div class="conversation-card" data-filename="${conversation.filename}">
            <div class="conversation-header">
                <div class="conversation-id">${conversation.id}</div>
                <div class="conversation-status ${statusClass}">${conversation.status}</div>
            </div>
            <div class="conversation-details">
                <div class="conversation-detail">
                    <span class="detail-label">Timestamp</span>
                    <span class="detail-value">${formatTimestamp(conversation.timestamp)}</span>
                </div>
                <div class="conversation-detail">
                    <span class="detail-label">Messages</span>
                    <span class="detail-value">${conversation.completed_messages} / ${conversation.total_messages} (${completionPercentage}%)</span>
                </div>
                <div class="conversation-detail">
                    <span class="detail-label">Assistant 1</span>
                    <span class="detail-value">${conversation.assistant_1_name || truncateId(conversation.assistant_1_id)}</span>
                </div>
                <div class="conversation-detail">
                    <span class="detail-label">Assistant 2</span>
                    <span class="detail-value">${conversation.assistant_2_name || truncateId(conversation.assistant_2_id)}</span>
                </div>
            </div>
        </div>
    `;
}

// Load and display conversation details
async function loadConversationDetails(filename) {
    try {
        const response = await fetch(`${API_URL}?action=get&file=${encodeURIComponent(filename)}`);
        const result = await response.json();

        if (result.success) {
            displayConversationModal(result.data);
        } else {
            throw new Error(result.error || 'Failed to load conversation');
        }
    } catch (error) {
        console.error('Error loading conversation details:', error);
        showError('Failed to load conversation details');
    }
}

// Display conversation in modal
function displayConversationModal(conversation) {
    const modal = document.getElementById('conversationModal');
    const metaContainer = document.getElementById('conversationMeta');
    const messagesContainer = document.getElementById('messagesContainer');

    // Update modal title
    document.getElementById('modalTitle').textContent = `Conversation: ${conversation.id}`;

    // Display metadata
    metaContainer.innerHTML = `
        <h3 style="margin-bottom: 15px;">Conversation Information</h3>
        <div class="meta-grid">
            <div class="meta-item">
                <span class="meta-label">ID</span>
                <span class="meta-value">${conversation.id}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Status</span>
                <span class="meta-value">
                    <span class="conversation-status status-${conversation.status}">${conversation.status}</span>
                </span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Started At</span>
                <span class="meta-value">${conversation.timestamp}</span>
            </div>
            ${conversation.completed_at ? `
            <div class="meta-item">
                <span class="meta-label">Completed At</span>
                <span class="meta-value">${conversation.completed_at}</span>
            </div>
            ` : ''}
            ${conversation.failed_at ? `
            <div class="meta-item">
                <span class="meta-label">Failed At</span>
                <span class="meta-value">${conversation.failed_at}</span>
            </div>
            ` : ''}
            <div class="meta-item">
                <span class="meta-label">Assistant 1</span>
                <span class="meta-value">${conversation.assistant_1_name || 'Assistant 1'} (${conversation.assistant_1_slug || 'N/A'})</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Assistant 2</span>
                <span class="meta-value">${conversation.assistant_2_name || 'Assistant 2'} (${conversation.assistant_2_slug || 'N/A'})</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Total Messages</span>
                <span class="meta-value">${conversation.messages.length} / ${conversation.total_messages}</span>
            </div>
            ${conversation.statistics ? `
            <div class="meta-item">
                <span class="meta-label">Total Characters</span>
                <span class="meta-value">${formatNumber(conversation.statistics.total_characters)}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Avg Message Length</span>
                <span class="meta-value">${conversation.statistics.average_message_length} chars</span>
            </div>
            ` : ''}
        </div>
        ${conversation.error ? `
        <div style="margin-top: 15px; padding: 15px; background: #f8d7da; color: #721c24; border-radius: 8px;">
            <strong>Error:</strong> ${conversation.error}
        </div>
        ` : ''}
    `;

    // Display messages
    messagesContainer.innerHTML = `
        <h3 style="margin-bottom: 20px;">Messages</h3>
        ${conversation.messages.map(msg => createMessageCard(msg)).join('')}
    `;

    // Show modal
    modal.classList.add('active');
}

// Create message card HTML
function createMessageCard(message) {
    const assistantClass = message.assistant === 'assistant_1' ? 'assistant-1' : 'assistant-2';
    const assistantName = message.assistant_name || (message.assistant === 'assistant_1' ? 'Assistant 1' : 'Assistant 2');

    let analysisHTML = '';
    if (message.analysis) {
        const analysis = message.analysis;
        analysisHTML = `
            <div class="message-section">
                <div class="message-label">Analysis</div>
                <div class="analysis-content">
                    ${analysis.topics && analysis.topics.length > 0 ? `
                        <div class="analysis-group">
                            <div class="analysis-group-label">Topics</div>
                            <div class="tag-container">
                                ${analysis.topics.map(topic => `<span class="tag tag-topic">${escapeHtml(topic)}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                    ${analysis.cultural_references && analysis.cultural_references.length > 0 ? `
                        <div class="analysis-group">
                            <div class="analysis-group-label">Cultural References</div>
                            <div class="tag-container">
                                ${analysis.cultural_references.map(ref => `<span class="tag tag-culture">${escapeHtml(ref)}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                    ${analysis.feeling_types && analysis.feeling_types.length > 0 ? `
                        <div class="analysis-group">
                            <div class="analysis-group-label">Feeling Types</div>
                            <div class="tag-container">
                                ${analysis.feeling_types.map(feeling => `<span class="tag tag-feeling">${escapeHtml(feeling)}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    return `
        <div class="message-card ${assistantClass}">
            <div class="message-header">
                <span>${assistantName}</span>
                <span class="message-number">Message #${message.number}</span>
            </div>
            <div class="message-body">
                <div class="message-section">
                    <div class="message-label">Input</div>
                    <div class="message-content message-input">${escapeHtml(message.input)}</div>
                </div>
                <div class="message-section">
                    <div class="message-label">Output</div>
                    <div class="message-content message-output">${escapeHtml(message.output)}</div>
                </div>
                ${analysisHTML}
            </div>
        </div>
    `;
}

// Close modal
function closeModal() {
    const modal = document.getElementById('conversationModal');
    modal.classList.remove('active');
}

// Utility functions
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function formatNumber(num) {
    return num.toLocaleString();
}

function truncateId(id) {
    if (id.length > 20) {
        return id.substring(0, 8) + '...' + id.substring(id.length - 8);
    }
    return id;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    alert(message);
}

// Word cloud colors
const wordCloudColors = [
    '#2c3e50', '#34495e', '#1e6f8e', '#7e1e8e', '#8e5e1e',
    '#27ae60', '#c0392b', '#d68910', '#2980b9', '#8e44ad'
];

// Load and render word frequency cloud
async function loadWordCloud() {
    const container = document.getElementById('wordFrequencyCloud');
    container.innerHTML = '<p class="loading">Loading word cloud...</p>';

    try {
        const minLength = document.getElementById('minWordLength').value;
        const topCount = document.getElementById('topWordsCount').value;

        const url = currentAssistantFilter === 'all'
            ? `${API_URL}?action=wordfrequency&minLength=${minLength}&topCount=${topCount}`
            : `${API_URL}?action=wordfrequency&minLength=${minLength}&topCount=${topCount}&assistant=${encodeURIComponent(currentAssistantFilter)}`;

        const response = await fetch(url);
        const result = await response.json();

        if (result.success && result.data.words.length > 0) {
            renderWordCloud(result.data.words, container);
        } else {
            container.innerHTML = '<p class="loading">No word data available</p>';
        }
    } catch (error) {
        console.error('Error loading word cloud:', error);
        container.innerHTML = '<p class="error">Failed to load word cloud</p>';
    }
}

// Render word cloud using wordcloud2
function renderWordCloud(words, container) {
    // Clear container and create canvas
    container.innerHTML = '';
    const canvas = document.createElement('canvas');
    canvas.id = 'wordCloudCanvas';
    canvas.width = container.offsetWidth || 500;
    canvas.height = 400;
    container.appendChild(canvas);

    // Calculate size scaling based on word frequencies
    const maxCount = Math.max(...words.map(w => w[1]));
    const minCount = Math.min(...words.map(w => w[1]));
    const sizeRange = maxCount - minCount || 1;

    // Scale words for display
    const scaledWords = words.map(([word, count]) => {
        const normalizedSize = (count - minCount) / sizeRange;
        const fontSize = Math.max(12, Math.round(normalizedSize * 50 + 14));
        return [word, fontSize];
    });

    // Configure and render word cloud
    WordCloud(canvas, {
        list: scaledWords,
        gridSize: 8,
        weightFactor: 1,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        color: function() {
            return wordCloudColors[Math.floor(Math.random() * wordCloudColors.length)];
        },
        rotateRatio: 0.3,
        rotationSteps: 2,
        backgroundColor: '#ffffff',
        drawOutOfBound: false,
        shrinkToFit: true,
        click: function(item) {
            if (item) {
                showWordInfo(item[0], words.find(w => w[0] === item[0])?.[1] || 0);
            }
        },
        hover: function(item) {
            canvas.style.cursor = item ? 'pointer' : 'default';
        }
    });
}

// Show word info tooltip
function showWordInfo(word, count) {
    alert(`Word: "${word}"\nOccurrences: ${count}`);
}

// Load and render word co-occurrence network
async function loadCooccurrence() {
    const container = document.getElementById('wordCooccurrence');
    container.innerHTML = '<p class="loading">Loading co-occurrence data...</p>';

    try {
        const minLength = document.getElementById('minWordLength').value;
        const topCount = document.getElementById('topWordsCount').value;

        const url = currentAssistantFilter === 'all'
            ? `${API_URL}?action=cooccurrence&minLength=${minLength}&topCount=${topCount}`
            : `${API_URL}?action=cooccurrence&minLength=${minLength}&topCount=${topCount}&assistant=${encodeURIComponent(currentAssistantFilter)}`;

        const response = await fetch(url);
        const result = await response.json();

        if (result.success && result.data.pairs.length > 0) {
            renderCooccurrence(result.data, container);
        } else {
            container.innerHTML = '<p class="loading">No co-occurrence data available</p>';
        }
    } catch (error) {
        console.error('Error loading co-occurrence:', error);
        container.innerHTML = '<p class="error">Failed to load co-occurrence data</p>';
    }
}

// Render co-occurrence as a network visualization
function renderCooccurrence(data, container) {
    container.innerHTML = '';

    // Create SVG for network visualization
    const width = container.offsetWidth || 500;
    const height = 400;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.style.backgroundColor = '#ffffff';
    container.appendChild(svg);

    const nodes = data.nodes;
    const links = data.pairs;

    if (nodes.length === 0 || links.length === 0) {
        container.innerHTML = '<p class="loading">Not enough data for co-occurrence visualization</p>';
        return;
    }

    // Calculate node positions using force-directed layout simulation
    const nodeMap = {};
    const maxCount = Math.max(...nodes.map(n => n.count));

    // Initialize node positions in a circle
    nodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / nodes.length;
        const radius = Math.min(width, height) * 0.35;
        nodeMap[node.id] = {
            ...node,
            x: width / 2 + radius * Math.cos(angle),
            y: height / 2 + radius * Math.sin(angle),
            vx: 0,
            vy: 0,
            size: Math.max(4, (node.count / maxCount) * 20)
        };
    });

    // Simple force simulation
    const iterations = 100;
    const repulsion = 500;
    const attraction = 0.05;

    for (let iter = 0; iter < iterations; iter++) {
        // Repulsion between all nodes
        Object.values(nodeMap).forEach(node1 => {
            Object.values(nodeMap).forEach(node2 => {
                if (node1.id !== node2.id) {
                    const dx = node1.x - node2.x;
                    const dy = node1.y - node2.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                    const force = repulsion / (dist * dist);
                    node1.vx += (dx / dist) * force;
                    node1.vy += (dy / dist) * force;
                }
            });
        });

        // Attraction along links
        links.forEach(link => {
            const source = nodeMap[link.source];
            const target = nodeMap[link.target];
            if (source && target) {
                const dx = target.x - source.x;
                const dy = target.y - source.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = attraction * link.weight;
                source.vx += (dx / dist) * force;
                source.vy += (dy / dist) * force;
                target.vx -= (dx / dist) * force;
                target.vy -= (dy / dist) * force;
            }
        });

        // Center gravity
        Object.values(nodeMap).forEach(node => {
            node.vx += (width / 2 - node.x) * 0.01;
            node.vy += (height / 2 - node.y) * 0.01;
        });

        // Apply velocity with damping
        Object.values(nodeMap).forEach(node => {
            node.x += node.vx * 0.1;
            node.y += node.vy * 0.1;
            node.vx *= 0.9;
            node.vy *= 0.9;

            // Keep within bounds
            node.x = Math.max(30, Math.min(width - 30, node.x));
            node.y = Math.max(30, Math.min(height - 30, node.y));
        });
    }

    // Draw links
    const maxWeight = Math.max(...links.map(l => l.weight));
    links.forEach(link => {
        const source = nodeMap[link.source];
        const target = nodeMap[link.target];
        if (source && target) {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', source.x);
            line.setAttribute('y1', source.y);
            line.setAttribute('x2', target.x);
            line.setAttribute('y2', target.y);
            const opacity = 0.2 + (link.weight / maxWeight) * 0.6;
            const strokeWidth = 1 + (link.weight / maxWeight) * 3;
            line.setAttribute('stroke', `rgba(44, 62, 80, ${opacity})`);
            line.setAttribute('stroke-width', strokeWidth);
            svg.appendChild(line);
        }
    });

    // Draw nodes
    Object.values(nodeMap).forEach(node => {
        // Node circle
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', node.x);
        circle.setAttribute('cy', node.y);
        circle.setAttribute('r', node.size);
        circle.setAttribute('fill', wordCloudColors[Math.floor(Math.random() * wordCloudColors.length)]);
        circle.setAttribute('stroke', '#fff');
        circle.setAttribute('stroke-width', 2);
        circle.style.cursor = 'pointer';

        // Add hover effect
        circle.addEventListener('mouseenter', () => {
            circle.setAttribute('r', node.size * 1.3);
        });
        circle.addEventListener('mouseleave', () => {
            circle.setAttribute('r', node.size);
        });
        circle.addEventListener('click', () => {
            showNodeConnections(node.id, data);
        });

        svg.appendChild(circle);

        // Node label (only for larger nodes)
        if (node.size > 8) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', node.x);
            text.setAttribute('y', node.y + node.size + 12);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('font-size', '10px');
            text.setAttribute('font-family', '-apple-system, BlinkMacSystemFont, sans-serif');
            text.setAttribute('fill', '#2c3e50');
            text.textContent = node.id;
            svg.appendChild(text);
        }
    });

    // Add legend/info
    const info = document.createElement('div');
    info.className = 'cooccurrence-info';
    info.innerHTML = `<small>Showing ${nodes.length} words with ${links.length} connections. Click a node to see its connections.</small>`;
    container.appendChild(info);
}

// Show connections for a specific word
function showNodeConnections(word, data) {
    const connections = data.pairs
        .filter(p => p.source === word || p.target === word)
        .map(p => ({
            word: p.source === word ? p.target : p.source,
            weight: p.weight
        }))
        .sort((a, b) => b.weight - a.weight)
        .slice(0, 10);

    const connectionList = connections
        .map(c => `  ${c.word} (${c.weight} co-occurrences)`)
        .join('\n');

    alert(`Word: "${word}"\n\nTop connections:\n${connectionList}`);
}

// Load and display linguistic analysis
async function loadLinguistics() {
    try {
        const url = currentAssistantFilter === 'all'
            ? `${API_URL}?action=linguistics`
            : `${API_URL}?action=linguistics&assistant=${encodeURIComponent(currentAssistantFilter)}`;

        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            displayLinguistics(result.data);
        } else {
            console.error('Failed to load linguistics:', result.error);
            showLinguisticsError();
        }
    } catch (error) {
        console.error('Error loading linguistics:', error);
        showLinguisticsError();
    }
}

// Display linguistic analysis data
function displayLinguistics(data) {
    // Update statistics
    const stats = data.statistics || {};
    document.getElementById('lingMessagesAnalyzed').textContent = formatNumber(stats.messages_analyzed || 0);
    document.getElementById('lingTotalNouns').textContent = formatNumber(stats.total_nouns || 0);
    document.getElementById('lingTotalVerbs').textContent = formatNumber(stats.total_verbs || 0);
    document.getElementById('lingTotalAdj').textContent = formatNumber(stats.total_adjectives || 0);
    document.getElementById('lingTotalMetaphors').textContent = formatNumber(stats.total_metaphors || 0);

    // Display nouns
    displayLingItems('topNouns', data.nouns || []);
    displayLingTypes('nounsByType', data.nouns_by_type || []);

    // Display verbs
    displayLingItems('topVerbs', data.verbs || []);
    displayLingTypes('verbsByType', data.verbs_by_type || []);

    // Display adjectives
    displayLingItems('topAdjectives', data.adjectives || []);
    displayLingTypes('adjectivesByType', data.adjectives_by_type || []);

    // Display expressions
    displayLingItems('topExpressions', data.expressions || [], true);
    displayLingTypes('expressionsByType', data.expressions_by_type || []);

    // Display metaphors
    displayLingItems('topMetaphors', data.metaphors || [], true);
    displayLingTypes('metaphorsByType', data.metaphors_by_type || []);
}

// Display linguistic items (nouns, verbs, etc.)
function displayLingItems(containerId, items, isExpression = false) {
    const container = document.getElementById(containerId);

    if (!items || items.length === 0) {
        container.innerHTML = '<p class="loading">No data available yet. Run conversations with linguistic analysis enabled.</p>';
        return;
    }

    container.innerHTML = items.map(item => {
        const word = item.word || '';
        const count = item.count || 0;
        const types = item.types || [];

        // Handle types - could be array or string
        let typeTags = '';
        if (Array.isArray(types) && types.length > 0) {
            typeTags = types.map(type =>
                `<span class="ling-type-tag type-${type}">${escapeHtml(type)}</span>`
            ).join('');
        } else if (typeof types === 'string' && types) {
            typeTags = `<span class="ling-type-tag type-${types}">${escapeHtml(types)}</span>`;
        }

        return `
            <div class="ling-item">
                <div>
                    <span class="ling-word">${escapeHtml(word)}</span>
                    ${typeTags ? `<div class="ling-types">${typeTags}</div>` : ''}
                </div>
                <span class="ling-count">${count}</span>
            </div>
        `;
    }).join('');
}

// Display type breakdown
function displayLingTypes(containerId, types) {
    const container = document.getElementById(containerId);

    if (!types || types.length === 0) {
        container.innerHTML = '<p class="loading">No type data available</p>';
        return;
    }

    container.innerHTML = types.map(item => {
        const type = item.type || 'unknown';
        const count = item.count || 0;

        return `
            <div class="ling-type-item">
                <span class="ling-type-name">${escapeHtml(type.replace(/_/g, ' '))}</span>
                <span class="ling-type-count">${formatNumber(count)}</span>
            </div>
        `;
    }).join('');
}

// Show error state for linguistics
function showLinguisticsError() {
    const containers = ['topNouns', 'topVerbs', 'topAdjectives', 'topExpressions', 'topMetaphors'];
    containers.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = '<p class="loading">No linguistic data available yet. Run conversations to generate analysis.</p>';
        }
    });

    const typeContainers = ['nounsByType', 'verbsByType', 'adjectivesByType', 'expressionsByType', 'metaphorsByType'];
    typeContainers.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = '<p class="loading">No type data</p>';
        }
    });
}

// Category colors for relationship visualization
const categoryColors = {
    noun: '#3498db',
    verb: '#27ae60',
    adjective: '#e74c3c',
    adverb: '#9b59b6',
    topic: '#f39c12',
    unknown: '#95a5a6'
};

// Load and display word relationships
async function loadRelationships() {
    try {
        const url = currentAssistantFilter === 'all'
            ? `${API_URL}?action=relationships`
            : `${API_URL}?action=relationships&assistant=${encodeURIComponent(currentAssistantFilter)}`;

        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            renderNetworkGraph(result.data);
            renderChordDiagram(result.data);
            renderRelationshipTables(result.data);
        } else {
            console.error('Failed to load relationships:', result.error);
        }
    } catch (error) {
        console.error('Error loading relationships:', error);
    }
}

// Render network graph visualization with draggable nodes
function renderNetworkGraph(data) {
    const container = document.getElementById('networkGraph');
    container.innerHTML = '';

    const nodes = data.network_nodes || [];
    const edges = data.network_edges || [];

    if (nodes.length === 0) {
        container.innerHTML = '<p class="loading">No relationship data available yet. Run conversations with linguistic analysis.</p>';
        return;
    }

    const width = container.offsetWidth || 800;
    const height = 450;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.style.backgroundColor = '#ffffff';
    container.appendChild(svg);

    // Create groups for layering (edges below nodes)
    const edgesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    const nodesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    const labelsGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    svg.appendChild(edgesGroup);
    svg.appendChild(nodesGroup);
    svg.appendChild(labelsGroup);

    // Calculate node positions using force simulation
    const nodeMap = {};
    const maxWeight = Math.max(...nodes.map(n => n.weight));

    // Initialize positions in a circle
    nodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / nodes.length;
        const radius = Math.min(width, height) * 0.35;
        nodeMap[node.id] = {
            ...node,
            x: width / 2 + radius * Math.cos(angle),
            y: height / 2 + radius * Math.sin(angle),
            vx: 0,
            vy: 0,
            size: Math.max(5, (node.weight / maxWeight) * 25),
            edges: [],      // Will store connected edge elements
            circle: null,   // Will store circle element
            label: null     // Will store label element
        };
    });

    // Force simulation
    const iterations = 150;
    const repulsion = 800;
    const attraction = 0.03;

    for (let iter = 0; iter < iterations; iter++) {
        // Repulsion
        Object.values(nodeMap).forEach(node1 => {
            Object.values(nodeMap).forEach(node2 => {
                if (node1.id !== node2.id) {
                    const dx = node1.x - node2.x;
                    const dy = node1.y - node2.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                    const force = repulsion / (dist * dist);
                    node1.vx += (dx / dist) * force;
                    node1.vy += (dy / dist) * force;
                }
            });
        });

        // Attraction along edges
        edges.forEach(edge => {
            const source = nodeMap[edge.source];
            const target = nodeMap[edge.target];
            if (source && target) {
                const dx = target.x - source.x;
                const dy = target.y - source.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = attraction * edge.weight;
                source.vx += (dx / dist) * force;
                source.vy += (dy / dist) * force;
                target.vx -= (dx / dist) * force;
                target.vy -= (dy / dist) * force;
            }
        });

        // Center gravity
        Object.values(nodeMap).forEach(node => {
            node.vx += (width / 2 - node.x) * 0.01;
            node.vy += (height / 2 - node.y) * 0.01;
        });

        // Apply velocity
        Object.values(nodeMap).forEach(node => {
            node.x += node.vx * 0.1;
            node.y += node.vy * 0.1;
            node.vx *= 0.9;
            node.vy *= 0.9;
            node.x = Math.max(40, Math.min(width - 40, node.x));
            node.y = Math.max(40, Math.min(height - 40, node.y));
        });
    }

    // Draw edges and store references
    const maxEdgeWeight = Math.max(...edges.map(e => e.weight));
    edges.forEach(edge => {
        const source = nodeMap[edge.source];
        const target = nodeMap[edge.target];
        if (source && target) {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', source.x);
            line.setAttribute('y1', source.y);
            line.setAttribute('x2', target.x);
            line.setAttribute('y2', target.y);
            const opacity = 0.15 + (edge.weight / maxEdgeWeight) * 0.5;
            const strokeWidth = 1 + (edge.weight / maxEdgeWeight) * 3;
            line.setAttribute('stroke', `rgba(44, 62, 80, ${opacity})`);
            line.setAttribute('stroke-width', strokeWidth);
            edgesGroup.appendChild(line);

            // Store edge reference for both nodes
            source.edges.push({ line, role: 'source', other: target });
            target.edges.push({ line, role: 'target', other: source });
        }
    });

    // Drag state
    let draggedNode = null;
    let isDragging = false;

    // Function to update node position and connected edges
    function updateNodePosition(node, x, y) {
        node.x = Math.max(40, Math.min(width - 40, x));
        node.y = Math.max(40, Math.min(height - 40, y));

        // Update circle position
        if (node.circle) {
            node.circle.setAttribute('cx', node.x);
            node.circle.setAttribute('cy', node.y);
        }

        // Update label position
        if (node.label) {
            node.label.setAttribute('x', node.x);
            node.label.setAttribute('y', node.y + node.size + 12);
        }

        // Update connected edges
        node.edges.forEach(edgeInfo => {
            if (edgeInfo.role === 'source') {
                edgeInfo.line.setAttribute('x1', node.x);
                edgeInfo.line.setAttribute('y1', node.y);
            } else {
                edgeInfo.line.setAttribute('x2', node.x);
                edgeInfo.line.setAttribute('y2', node.y);
            }
        });
    }

    // Mouse event handlers
    function onMouseMove(e) {
        if (!isDragging || !draggedNode) return;
        e.preventDefault();

        const rect = svg.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        updateNodePosition(draggedNode, x, y);
    }

    function onMouseUp() {
        if (draggedNode && draggedNode.circle) {
            draggedNode.circle.setAttribute('r', draggedNode.size);
        }
        isDragging = false;
        draggedNode = null;
        svg.style.cursor = 'default';
    }

    // Add global mouse listeners to SVG
    svg.addEventListener('mousemove', onMouseMove);
    svg.addEventListener('mouseup', onMouseUp);
    svg.addEventListener('mouseleave', onMouseUp);

    // Draw nodes with drag support
    Object.values(nodeMap).forEach(node => {
        const color = categoryColors[node.category] || categoryColors.unknown;

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', node.x);
        circle.setAttribute('cy', node.y);
        circle.setAttribute('r', node.size);
        circle.setAttribute('fill', color);
        circle.setAttribute('stroke', '#fff');
        circle.setAttribute('stroke-width', 2);
        circle.style.cursor = 'grab';

        // Store reference
        node.circle = circle;

        // Drag start
        circle.addEventListener('mousedown', (e) => {
            e.preventDefault();
            isDragging = true;
            draggedNode = node;
            circle.setAttribute('r', node.size * 1.2);
            svg.style.cursor = 'grabbing';
        });

        // Hover effect (only when not dragging)
        circle.addEventListener('mouseenter', () => {
            if (!isDragging) {
                circle.setAttribute('r', node.size * 1.2);
                circle.style.cursor = 'grab';
            }
        });
        circle.addEventListener('mouseleave', () => {
            if (!isDragging || draggedNode !== node) {
                circle.setAttribute('r', node.size);
            }
        });

        // Click to search (only fires if not dragging)
        let clickStart = null;
        circle.addEventListener('mousedown', () => {
            clickStart = Date.now();
        });
        circle.addEventListener('mouseup', (e) => {
            // Only trigger click if mouse wasn't dragged (short press)
            if (clickStart && Date.now() - clickStart < 200 && !isDragging) {
                document.getElementById('wordSearchInput').value = node.id;
                searchWordContext(node.id);
                document.querySelectorAll('.rel-viz-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.rel-viz-panel').forEach(p => p.classList.remove('active'));
                document.querySelector('.rel-viz-tab[data-viz="search"]').classList.add('active');
                document.getElementById('vizSearch').classList.add('active');
            }
            clickStart = null;
        });

        nodesGroup.appendChild(circle);

        // Labels for larger nodes
        if (node.size > 10) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', node.x);
            text.setAttribute('y', node.y + node.size + 12);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('font-size', '10px');
            text.setAttribute('font-family', '-apple-system, BlinkMacSystemFont, sans-serif');
            text.setAttribute('fill', '#2c3e50');
            text.setAttribute('pointer-events', 'none'); // Don't interfere with drag
            text.textContent = node.id;
            labelsGroup.appendChild(text);
            node.label = text;
        }
    });

    // Add instruction text
    const infoText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    infoText.setAttribute('x', 10);
    infoText.setAttribute('y', height - 10);
    infoText.setAttribute('font-size', '11px');
    infoText.setAttribute('fill', '#95a5a6');
    infoText.textContent = 'Drag nodes to rearrange • Click node to search relationships';
    svg.appendChild(infoText);
}

// Render chord diagram with specific words
function renderChordDiagram(data) {
    const container = document.getElementById('chordDiagram');
    container.innerHTML = '';

    const nodes = data.network_nodes || [];
    const edges = data.network_edges || [];

    if (edges.length === 0 || nodes.length === 0) {
        container.innerHTML = '<p class="loading">No relationship data available yet.</p>';
        return;
    }

    const width = container.offsetWidth || 700;
    const height = 500;
    const centerX = width / 2;
    const centerY = height / 2;
    const outerRadius = Math.min(width, height) * 0.38;
    const innerRadius = outerRadius - 25;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    container.appendChild(svg);

    // Group nodes by category
    const categories = ['noun', 'verb', 'adjective', 'adverb', 'topic'];
    const nodesByCategory = {};
    categories.forEach(cat => {
        nodesByCategory[cat] = nodes
            .filter(n => n.category === cat)
            .sort((a, b) => b.weight - a.weight)
            .slice(0, 15); // Top 15 per category to avoid overcrowding
    });

    // Calculate total words and positions
    const activeCategories = categories.filter(cat => nodesByCategory[cat].length > 0);
    const totalWords = activeCategories.reduce((sum, cat) => sum + nodesByCategory[cat].length, 0);

    if (totalWords === 0) {
        container.innerHTML = '<p class="loading">No words to display.</p>';
        return;
    }

    // Assign angular positions to each word
    const wordPositions = {};
    const categoryRanges = {};
    let currentAngle = -Math.PI / 2; // Start at top
    const gapBetweenCategories = 0.15; // Gap between category groups
    const totalGap = gapBetweenCategories * activeCategories.length;
    const availableAngle = 2 * Math.PI - totalGap;

    activeCategories.forEach(cat => {
        const wordsInCat = nodesByCategory[cat];
        const categoryAngleSize = (wordsInCat.length / totalWords) * availableAngle;

        categoryRanges[cat] = {
            start: currentAngle,
            end: currentAngle + categoryAngleSize
        };

        wordsInCat.forEach((node, idx) => {
            const angleOffset = (idx + 0.5) / wordsInCat.length;
            const angle = currentAngle + angleOffset * categoryAngleSize;
            wordPositions[node.id] = {
                angle: angle,
                category: cat,
                weight: node.weight
            };
        });

        currentAngle += categoryAngleSize + gapBetweenCategories;
    });

    // Draw category arcs (outer ring segments)
    activeCategories.forEach(cat => {
        const range = categoryRanges[cat];
        const color = categoryColors[cat];

        // Draw arc
        const x1 = centerX + outerRadius * Math.cos(range.start);
        const y1 = centerY + outerRadius * Math.sin(range.start);
        const x2 = centerX + outerRadius * Math.cos(range.end);
        const y2 = centerY + outerRadius * Math.sin(range.end);

        const largeArc = range.end - range.start > Math.PI ? 1 : 0;

        const arc = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        arc.setAttribute('d', `M ${x1} ${y1} A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${x2} ${y2}`);
        arc.setAttribute('fill', 'none');
        arc.setAttribute('stroke', color);
        arc.setAttribute('stroke-width', 20);
        arc.setAttribute('opacity', '0.3');
        svg.appendChild(arc);

        // Category label
        const midAngle = (range.start + range.end) / 2;
        const labelRadius = outerRadius + 35;
        const labelX = centerX + labelRadius * Math.cos(midAngle);
        const labelY = centerY + labelRadius * Math.sin(midAngle);

        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', labelX);
        label.setAttribute('y', labelY);
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('dominant-baseline', 'middle');
        label.setAttribute('font-size', '11px');
        label.setAttribute('font-weight', '600');
        label.setAttribute('fill', color);
        label.textContent = cat.toUpperCase();
        svg.appendChild(label);
    });

    // Draw word labels around the perimeter
    Object.entries(wordPositions).forEach(([word, pos]) => {
        const color = categoryColors[pos.category];
        const labelRadius = outerRadius + 12;
        const x = centerX + labelRadius * Math.cos(pos.angle);
        const y = centerY + labelRadius * Math.sin(pos.angle);

        // Calculate rotation for readability
        let rotation = (pos.angle * 180 / Math.PI);
        let anchor = 'start';
        if (pos.angle > Math.PI / 2 && pos.angle < 3 * Math.PI / 2) {
            rotation += 180;
            anchor = 'end';
        }

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', x);
        text.setAttribute('y', y);
        text.setAttribute('text-anchor', anchor);
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('font-size', '9px');
        text.setAttribute('fill', color);
        text.setAttribute('transform', `rotate(${rotation}, ${x}, ${y})`);
        text.textContent = word.length > 12 ? word.substring(0, 10) + '...' : word;
        text.style.cursor = 'pointer';

        // Hover effect
        text.addEventListener('mouseenter', () => {
            text.setAttribute('font-weight', '700');
            text.setAttribute('font-size', '11px');
            highlightWordChords(word);
        });
        text.addEventListener('mouseleave', () => {
            text.setAttribute('font-weight', 'normal');
            text.setAttribute('font-size', '9px');
            resetChordHighlights();
        });

        svg.appendChild(text);

        // Small dot at the word position on the arc
        const dotX = centerX + innerRadius * Math.cos(pos.angle);
        const dotY = centerY + innerRadius * Math.sin(pos.angle);
        const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        dot.setAttribute('cx', dotX);
        dot.setAttribute('cy', dotY);
        dot.setAttribute('r', 3);
        dot.setAttribute('fill', color);
        svg.appendChild(dot);
    });

    // Draw chords between connected words
    const chordElements = [];
    const maxEdgeWeight = Math.max(...edges.map(e => e.weight));

    edges.forEach(edge => {
        const sourcePos = wordPositions[edge.source];
        const targetPos = wordPositions[edge.target];

        if (!sourcePos || !targetPos) return;

        const x1 = centerX + innerRadius * 0.95 * Math.cos(sourcePos.angle);
        const y1 = centerY + innerRadius * 0.95 * Math.sin(sourcePos.angle);
        const x2 = centerX + innerRadius * 0.95 * Math.cos(targetPos.angle);
        const y2 = centerY + innerRadius * 0.95 * Math.sin(targetPos.angle);

        // Use quadratic bezier through center area
        const ctrl1X = centerX + innerRadius * 0.3 * Math.cos(sourcePos.angle);
        const ctrl1Y = centerY + innerRadius * 0.3 * Math.sin(sourcePos.angle);
        const ctrl2X = centerX + innerRadius * 0.3 * Math.cos(targetPos.angle);
        const ctrl2Y = centerY + innerRadius * 0.3 * Math.sin(targetPos.angle);

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M ${x1} ${y1} C ${ctrl1X} ${ctrl1Y}, ${ctrl2X} ${ctrl2Y}, ${x2} ${y2}`);
        path.setAttribute('fill', 'none');

        // Color based on source category
        const color = categoryColors[sourcePos.category] || '#95a5a6';
        const opacity = 0.1 + (edge.weight / maxEdgeWeight) * 0.4;
        const strokeWidth = 1 + (edge.weight / maxEdgeWeight) * 3;

        path.setAttribute('stroke', color);
        path.setAttribute('stroke-opacity', opacity);
        path.setAttribute('stroke-width', strokeWidth);
        path.dataset.source = edge.source;
        path.dataset.target = edge.target;

        chordElements.push(path);
        svg.insertBefore(path, svg.firstChild); // Insert behind labels
    });

    // Highlight functions
    function highlightWordChords(word) {
        chordElements.forEach(chord => {
            if (chord.dataset.source === word || chord.dataset.target === word) {
                chord.setAttribute('stroke-opacity', '0.8');
                chord.setAttribute('stroke-width', '4');
            } else {
                chord.setAttribute('stroke-opacity', '0.05');
            }
        });
    }

    function resetChordHighlights() {
        chordElements.forEach(chord => {
            const sourcePos = wordPositions[chord.dataset.source];
            const edge = edges.find(e => e.source === chord.dataset.source && e.target === chord.dataset.target);
            if (edge && sourcePos) {
                const opacity = 0.1 + (edge.weight / maxEdgeWeight) * 0.4;
                const strokeWidth = 1 + (edge.weight / maxEdgeWeight) * 3;
                chord.setAttribute('stroke-opacity', opacity);
                chord.setAttribute('stroke-width', strokeWidth);
            }
        });
    }

    // Add info text
    const infoText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    infoText.setAttribute('x', centerX);
    infoText.setAttribute('y', height - 10);
    infoText.setAttribute('text-anchor', 'middle');
    infoText.setAttribute('font-size', '11px');
    infoText.setAttribute('fill', '#95a5a6');
    infoText.textContent = 'Hover over words to highlight their connections';
    svg.appendChild(infoText);
}

// Render relationship tables
function renderRelationshipTables(data) {
    // Noun-Verb table
    const nounVerbTable = document.getElementById('nounVerbTable');
    if (data.noun_verb && data.noun_verb.length > 0) {
        nounVerbTable.innerHTML = data.noun_verb.slice(0, 20).map(r => `
            <div class="rel-row">
                <span class="rel-word">${escapeHtml(r.noun)}</span>
                <span class="rel-arrow">→</span>
                <span class="rel-target">${escapeHtml(r.verb)}</span>
                <span class="rel-count">${r.count}</span>
            </div>
        `).join('');
    } else {
        nounVerbTable.innerHTML = '<p class="loading">No data</p>';
    }

    // Verb-Noun table
    const verbNounTable = document.getElementById('verbNounTable');
    if (data.verb_noun_obj && data.verb_noun_obj.length > 0) {
        verbNounTable.innerHTML = data.verb_noun_obj.slice(0, 20).map(r => `
            <div class="rel-row">
                <span class="rel-word">${escapeHtml(r.verb)}</span>
                <span class="rel-arrow">→</span>
                <span class="rel-target">${escapeHtml(r.noun)}</span>
                <span class="rel-count">${r.count}</span>
            </div>
        `).join('');
    } else {
        verbNounTable.innerHTML = '<p class="loading">No data</p>';
    }

    // Adj-Noun table
    const adjNounTable = document.getElementById('adjNounTable');
    if (data.adj_noun && data.adj_noun.length > 0) {
        adjNounTable.innerHTML = data.adj_noun.slice(0, 20).map(r => `
            <div class="rel-row">
                <span class="rel-word">${escapeHtml(r.adjective)}</span>
                <span class="rel-arrow">→</span>
                <span class="rel-target">${escapeHtml(r.noun)}</span>
                <span class="rel-count">${r.count}</span>
            </div>
        `).join('');
    } else {
        adjNounTable.innerHTML = '<p class="loading">No data</p>';
    }

    // Word-Topic table
    const wordTopicTable = document.getElementById('wordTopicTable');
    if (data.word_topic && data.word_topic.length > 0) {
        wordTopicTable.innerHTML = data.word_topic.slice(0, 20).map(r => `
            <div class="rel-row">
                <span class="rel-word">${escapeHtml(r.word)}</span>
                <span class="rel-arrow">→</span>
                <span class="rel-target">${escapeHtml(r.topic)}</span>
                <span class="rel-count">${r.count}</span>
            </div>
        `).join('');
    } else {
        wordTopicTable.innerHTML = '<p class="loading">No data</p>';
    }
}

// Search word context
async function searchWordContext(word) {
    const container = document.getElementById('wordContextResults');
    container.innerHTML = '<p class="loading">Searching...</p>';

    try {
        const url = currentAssistantFilter === 'all'
            ? `${API_URL}?action=word_context&word=${encodeURIComponent(word)}`
            : `${API_URL}?action=word_context&word=${encodeURIComponent(word)}&assistant=${encodeURIComponent(currentAssistantFilter)}`;

        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            displayWordContext(result.data);
        } else {
            container.innerHTML = `<p class="loading">Error: ${result.error}</p>`;
        }
    } catch (error) {
        console.error('Error searching word context:', error);
        container.innerHTML = '<p class="loading">Failed to search word context</p>';
    }
}

// Display word context results
function displayWordContext(data) {
    const container = document.getElementById('wordContextResults');
    const relations = data.relations;

    // Check if any relations exist
    const hasRelations = Object.values(relations).some(arr => arr && arr.length > 0);

    if (!hasRelations) {
        container.innerHTML = `
            <div class="context-word-title">No relationships found for "${escapeHtml(data.word)}"</div>
            <p class="loading">This word may not appear in any analyzed conversations, or it has no extracted relationships.</p>
        `;
        return;
    }

    const renderCategory = (title, items) => {
        if (!items || items.length === 0) return '';
        return `
            <div class="context-category">
                <h5>${title}</h5>
                <div class="context-list">
                    ${items.map(item => `
                        <div class="context-item">
                            <span class="context-item-word">${escapeHtml(item.word)}</span>
                            <span class="context-item-count">${item.count}x</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    };

    container.innerHTML = `
        <div class="context-word-title">Relationships for "${escapeHtml(data.word)}"</div>
        <div class="context-grid">
            ${renderCategory('As Noun → Used with Verbs', relations.as_noun_with_verbs)}
            ${renderCategory('As Verb → Used with Nouns', relations.as_verb_with_nouns)}
            ${renderCategory('As/With Adjectives', relations.as_adjective_with_nouns)}
            ${renderCategory('As/With Adverbs', relations.as_adverb_with_verbs)}
            ${renderCategory('Appears in Topics', relations.with_topics)}
            ${renderCategory('Appears in Expressions', relations.appears_in_expressions)}
            ${renderCategory('Appears in Metaphors', relations.appears_in_metaphors)}
        </div>
    `;
}
