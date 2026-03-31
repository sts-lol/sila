<?php

/**
 * Project Replicant - AI Assistants Conversation Script
 * This script facilitates a conversation between two OpenAI assistants
 */

// Configuration
$apiKey = ''; // Replace with your actual API key
$assistant1Id = ''; // Replace with your first assistant ID
$assistant2Id = ''; // Replace with your second assistant ID
$topicExtractorId = ''; // Topic extractor assistant ID

$numberOfConversations = 36; // Number of conversation sessions to run
$maxMessages = 10; // Total number of messages to exchange per conversation
$conversationsDir = 'conversations'; // Directory to store conversations

// Create conversations directory if it doesn't exist
if (!is_dir($conversationsDir)) {
    mkdir($conversationsDir, 0755, true);
}

/**
 * Make API request to OpenAI
 */
function makeRequest($url, $method, $apiKey, $data = null) {
    $ch = curl_init($url);

    $headers = [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $apiKey,
        'OpenAI-Beta: assistants=v2'
    ];

    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        if ($data) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
    }

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode >= 400) {
        throw new Exception("API request failed with code $httpCode: $response");
    }

    return json_decode($response, true);
}

/**
 * Get assistant details
 */
function getAssistantDetails($assistantId, $apiKey) {
    $url = "https://api.openai.com/v1/assistants/$assistantId";
    return makeRequest($url, 'GET', $apiKey);
}

/**
 * Create slug from assistant name
 */
function createSlug($name) {
    $slug = strtolower($name);
    $slug = preg_replace('/[^a-z0-9]+/', '-', $slug);
    $slug = trim($slug, '-');
    return $slug;
}

/**
 * Create a thread
 */
function createThread($apiKey) {
    $url = 'https://api.openai.com/v1/threads';
    return makeRequest($url, 'POST', $apiKey);
}

/**
 * Add message to thread
 */
function addMessage($threadId, $content, $apiKey) {
    $url = "https://api.openai.com/v1/threads/$threadId/messages";
    $data = [
        'role' => 'user',
        'content' => $content
    ];
    return makeRequest($url, 'POST', $apiKey, $data);
}

/**
 * Run assistant on thread
 */
function runAssistant($threadId, $assistantId, $apiKey) {
    $url = "https://api.openai.com/v1/threads/$threadId/runs";
    $data = [
        'assistant_id' => $assistantId
    ];
    return makeRequest($url, 'POST', $apiKey, $data);
}

/**
 * Get run status
 */
function getRunStatus($threadId, $runId, $apiKey) {
    $url = "https://api.openai.com/v1/threads/$threadId/runs/$runId";
    return makeRequest($url, 'GET', $apiKey);
}

/**
 * Wait for run completion
 */
function waitForCompletion($threadId, $runId, $apiKey, $maxWaitTime = 60) {
    $startTime = time();

    while (true) {
        $run = getRunStatus($threadId, $runId, $apiKey);
        $status = $run['status'];

        echo "Run status: $status\n";

        if ($status === 'completed') {
            return true;
        } elseif (in_array($status, ['failed', 'cancelled', 'expired'])) {
            throw new Exception("Run $status: " . json_encode($run));
        }

        if (time() - $startTime > $maxWaitTime) {
            throw new Exception("Run timed out after $maxWaitTime seconds");
        }

        sleep(1); // Wait 1 second before checking again
    }
}

/**
 * Get latest assistant response
 */
function getLatestResponse($threadId, $apiKey) {
    $url = "https://api.openai.com/v1/threads/$threadId/messages?limit=1";
    $response = makeRequest($url, 'GET', $apiKey);

    if (empty($response['data'])) {
        throw new Exception("No messages found in thread");
    }

    $message = $response['data'][0];
    $content = $message['content'][0]['text']['value'];

    return $content;
}

/**
 * Get assistant response
 */
function getAssistantResponse($threadId, $assistantId, $message, $apiKey) {
    // Add message to thread
    addMessage($threadId, $message, $apiKey);

    // Run assistant
    $run = runAssistant($threadId, $assistantId, $apiKey);
    $runId = $run['id'];

    // Wait for completion
    waitForCompletion($threadId, $runId, $apiKey);

    // Get response
    return getLatestResponse($threadId, $apiKey);
}

/**
 * Perform linguistic analysis using Python spaCy
 */
function analyzeLinguistics($text) {
    try {
        $scriptPath = __DIR__ . '/linguistic_analyzer.py';

        if (!file_exists($scriptPath)) {
            echo "Warning: Linguistic analyzer script not found\n";
            return null;
        }

        // Create a temporary file for the text to avoid shell escaping issues
        $tempFile = tempnam(sys_get_temp_dir(), 'nlp_');
        file_put_contents($tempFile, $text);

        // Run Python script
        $command = sprintf(
            'python3 %s < %s 2>&1',
            escapeshellarg($scriptPath),
            escapeshellarg($tempFile)
        );

        $output = shell_exec($command);
        unlink($tempFile); // Clean up temp file

        if (!$output) {
            echo "Warning: Linguistic analysis returned no output\n";
            return null;
        }

        $result = json_decode($output, true);

        if (isset($result['error'])) {
            echo "Warning: Linguistic analysis error: " . $result['error'] . "\n";
            return null;
        }

        return $result;

    } catch (Exception $e) {
        echo "Warning: Linguistic analysis failed: " . $e->getMessage() . "\n";
        return null;
    }
}

/**
 * Strip JavaScript-style comments from JSON string, preserving strings
 */
function stripJsonComments($jsonStr) {
    $result = '';
    $len = strlen($jsonStr);
    $inString = false;
    $escapeNext = false;

    for ($i = 0; $i < $len; $i++) {
        $char = $jsonStr[$i];

        if ($escapeNext) {
            $result .= $char;
            $escapeNext = false;
            continue;
        }

        if ($char === '\\' && $inString) {
            $result .= $char;
            $escapeNext = true;
            continue;
        }

        if ($char === '"' && !$escapeNext) {
            $inString = !$inString;
            $result .= $char;
            continue;
        }

        if (!$inString) {
            // Check for single-line comment
            if ($char === '/' && $i + 1 < $len && $jsonStr[$i + 1] === '/') {
                // Skip until end of line
                while ($i < $len && $jsonStr[$i] !== "\n") {
                    $i++;
                }
                $i--; // Compensate for loop increment
                continue;
            }
            // Check for multi-line comment
            if ($char === '/' && $i + 1 < $len && $jsonStr[$i + 1] === '*') {
                $i += 2;
                while ($i + 1 < $len && !($jsonStr[$i] === '*' && $jsonStr[$i + 1] === '/')) {
                    $i++;
                }
                $i++; // Skip past */
                continue;
            }
        }

        $result .= $char;
    }

    // Remove trailing commas (invalid in JSON but left after comment removal)
    $result = preg_replace('/,(\s*[\]\}])/', '$1', $result);
    // Remove parenthetical explanations after string values: "value" (explanation)
    $result = preg_replace('/"\s*\([^)]*\)/', '"', $result);

    return $result;
}

/**
 * Extract topics from text using topic extractor assistant
 */
function extractTopics($threadId, $extractorId, $text, $apiKey) {
    try {
        $response = getAssistantResponse($threadId, $extractorId, $text, $apiKey);

        // Strip JavaScript-style comments from response
        $cleanedResponse = stripJsonComments($response);

        // Try to parse JSON from response
        // The response might be wrapped in code blocks, so extract JSON
        $jsonPattern = '/\{(?:[^{}]|(?R))*\}/s';
        if (preg_match($jsonPattern, $cleanedResponse, $matches)) {
            $jsonData = json_decode($matches[0], true);
            if ($jsonData) {
                return $jsonData;
            }
        }

        // If direct JSON parsing fails, try to decode the whole response
        $jsonData = json_decode($cleanedResponse, true);
        if ($jsonData) {
            return $jsonData;
        }

        // If all parsing fails, return null
        echo "Warning: Could not parse topic extraction response\n";
        echo "API Response: " . substr($response, 0, 500) . "\n";
        return null;

    } catch (Exception $e) {
        echo "Warning: Topic extraction failed: " . $e->getMessage() . "\n";
        return null;
    }
}

// Main execution
echo "SILA - Starting...\n";
echo "Will run $numberOfConversations conversation(s)\n\n";

// Fetch assistant details once (reused across all conversations)
echo "Fetching Assistant 1 details...\n";
$assistant1Details = getAssistantDetails($assistant1Id, $apiKey);
$assistant1Name = $assistant1Details['name'] ?? 'Assistant 1';
$assistant1Slug = createSlug($assistant1Name);

echo "Fetching Assistant 2 details...\n";
$assistant2Details = getAssistantDetails($assistant2Id, $apiKey);
$assistant2Name = $assistant2Details['name'] ?? 'Assistant 2';
$assistant2Slug = createSlug($assistant2Name);

echo "Assistant 1: $assistant1Name ($assistant1Slug)\n";
echo "Assistant 2: $assistant2Name ($assistant2Slug)\n\n";

// Run multiple conversations
for ($convNum = 1; $convNum <= $numberOfConversations; $convNum++) {
    try {
        echo str_repeat("=", 70) . "\n";
        echo "CONVERSATION $convNum of $numberOfConversations\n";
        echo str_repeat("=", 70) . "\n\n";

        // Generate unique filename for this conversation
        $conversationId = uniqid('conv_', true);
        $timestamp = date('Y-m-d_H-i-s');
        $outputFile = "$conversationsDir/conversation_{$timestamp}_{$conversationId}.json";

        // Initialize conversation storage
        $conversation = [
            'id' => $conversationId,
            'timestamp' => date('Y-m-d H:i:s'),
            'assistant_1_id' => $assistant1Id,
            'assistant_1_name' => $assistant1Name,
            'assistant_1_slug' => $assistant1Slug,
            'assistant_2_id' => $assistant2Id,
            'assistant_2_name' => $assistant2Name,
            'assistant_2_slug' => $assistant2Slug,
            'total_messages' => $maxMessages,
            'status' => 'in_progress',
            'messages' => []
        ];

        // Create threads for both assistants
        echo "Creating thread for $assistant1Name...\n";
        $thread1 = createThread($apiKey);
        $thread1Id = $thread1['id'];

        echo "Creating thread for $assistant2Name...\n";
        $thread2 = createThread($apiKey);
        $thread2Id = $thread2['id'];

        echo "Creating thread for topic extractor...\n";
        $threadExtractor = createThread($apiKey);
        $threadExtractorId = $threadExtractor['id'];

        echo "\nStarting message exchange...\n";
        echo str_repeat("-", 60) . "\n\n";

    // Initial prompt - only used for the first message to Assistant 1
    $currentMessage = "start conversation";

    // Exchange messages in alternating fashion
    // Flow: A1 responds to prompt → A2 responds to A1 → A1 responds to A2 → A2 responds to A1 → etc.
    for ($i = 0; $i < $maxMessages; $i++) {
        $messageNum = $i + 1;

        // Determine which assistant is speaking
        if ($i % 2 === 0) {
            // Assistant 1's turn - receives either initial prompt or Assistant 2's last response
            echo "Message $messageNum - $assistant1Name:\n";
            echo "Sending: $currentMessage\n";

            $response = getAssistantResponse($thread1Id, $assistant1Id, $currentMessage, $apiKey);

            echo "Response: $response\n";

            // Extract topics from the response
            echo "Extracting topics...\n";
            $analysis = extractTopics($threadExtractorId, $topicExtractorId, $response, $apiKey);

            if ($analysis) {
                echo "Topics extracted successfully\n";
            }

            // Perform linguistic analysis
            echo "Performing linguistic analysis...\n";
            $linguistics = analyzeLinguistics($response);

            if ($linguistics) {
                echo "Linguistic analysis completed\n";
            }

            echo "\n";

            $messageData = [
                'number' => $messageNum,
                'assistant' => 'assistant_1',
                'assistant_id' => $assistant1Id,
                'assistant_name' => $assistant1Name,
                'assistant_slug' => $assistant1Slug,
                'input' => $currentMessage,
                'output' => $response
            ];

            if ($analysis) {
                $messageData['analysis'] = $analysis;
            }

            if ($linguistics) {
                $messageData['linguistics'] = $linguistics;
            }

            $conversation['messages'][] = $messageData;

            // Update current message with Assistant 1's response - this will be sent to Assistant 2 next
            $currentMessage = $response;
        } else {
            // Assistant 2's turn - receives Assistant 1's last response
            echo "Message $messageNum - $assistant2Name:\n";
            echo "Sending: $currentMessage\n";

            $response = getAssistantResponse($thread2Id, $assistant2Id, $currentMessage, $apiKey);

            echo "Response: $response\n";

            // Extract topics from the response
            echo "Extracting topics...\n";
            $analysis = extractTopics($threadExtractorId, $topicExtractorId, $response, $apiKey);

            if ($analysis) {
                echo "Topics extracted successfully\n";
            }

            // Perform linguistic analysis
            echo "Performing linguistic analysis...\n";
            $linguistics = analyzeLinguistics($response);

            if ($linguistics) {
                echo "Linguistic analysis completed\n";
            }

            echo "\n";

            $messageData = [
                'number' => $messageNum,
                'assistant' => 'assistant_2',
                'assistant_id' => $assistant2Id,
                'assistant_name' => $assistant2Name,
                'assistant_slug' => $assistant2Slug,
                'input' => $currentMessage,
                'output' => $response
            ];

            if ($analysis) {
                $messageData['analysis'] = $analysis;
            }

            if ($linguistics) {
                $messageData['linguistics'] = $linguistics;
            }

            $conversation['messages'][] = $messageData;

            // Update current message with Assistant 2's response - this will be sent to Assistant 1 next
            $currentMessage = $response;
        }

        echo str_repeat("-", 60) . "\n\n";
    }

    // Mark conversation as completed
    $conversation['status'] = 'completed';
    $conversation['completed_at'] = date('Y-m-d H:i:s');

    // Calculate statistics
    $totalChars = 0;
    foreach ($conversation['messages'] as $msg) {
        $totalChars += strlen($msg['output']);
    }
    $conversation['statistics'] = [
        'total_characters' => $totalChars,
        'average_message_length' => round($totalChars / count($conversation['messages']))
    ];

    // Save conversation to JSON file
    $jsonOutput = json_encode($conversation, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    file_put_contents($outputFile, $jsonOutput);

        echo "Conversation completed and saved to $outputFile\n";
        echo "Total messages exchanged: $maxMessages\n";
        echo "Conversation ID: $conversationId\n\n";

    } catch (Exception $e) {
        echo "Error in conversation $convNum: " . $e->getMessage() . "\n";

        // Save partial conversation if any messages were exchanged
        if (!empty($conversation['messages'])) {
            $conversation['status'] = 'failed';
            $conversation['error'] = $e->getMessage();
            $conversation['failed_at'] = date('Y-m-d H:i:s');
            $jsonOutput = json_encode($conversation, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
            file_put_contents($outputFile, $jsonOutput);
            echo "Partial conversation saved to $outputFile\n\n";
        }

        // Continue with next conversation instead of exiting
        echo "Continuing with next conversation...\n\n";
    }
}

echo str_repeat("=", 70) . "\n";
echo "All conversations completed!\n";
echo "Total conversations run: $numberOfConversations\n";
echo str_repeat("=", 70) . "\n";

?>
