#!/usr/bin/env python3
"""
Comprehensive corpus analysis for research question document.
Analyzes semantic, narrative, and linguistic strategies in conversations.
Extended version with expanded lexicons for deeper analysis.
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter

CONVERSATIONS_DIR = Path(__file__).parent / "conversations"

# Extended intimacy lexicon categories
INTIMACY_WORDS = {
    # Core emotional vocabulary
    'core_affection': [
        'love', 'loved', 'loving', 'adore', 'adored', 'adoring', 'cherish', 'cherished',
        'cherishing', 'treasure', 'treasured', 'devoted', 'devotion', 'affection', 'affectionate',
        'fond', 'fondness', 'endearing', 'dear', 'dearest', 'darling', 'precious'
    ],
    'emotional_state': [
        'feel', 'feeling', 'feelings', 'felt', 'emotion', 'emotions', 'emotional',
        'mood', 'moods', 'sense', 'sensing', 'sensed', 'experience', 'experiencing',
        'experienced', 'moved', 'touched', 'stirred'
    ],
    'safety_security': [
        'comfort', 'comfortable', 'comforting', 'cozy', 'safe', 'secure', 'security',
        'safety', 'protected', 'protection', 'shelter', 'sheltered', 'haven', 'refuge',
        'reassure', 'reassured', 'reassuring', 'calm', 'calming', 'peaceful', 'peace',
        'settled', 'grounded', 'stable', 'steady', 'relaxed', 'relaxing', 'soothing', 'soothe'
    ],
    'enchantment': [
        'magical', 'magic', 'wonder', 'wonderful', 'amazing', 'incredible', 'fantastic',
        'fantastical', 'enchanted', 'enchanting', 'mesmerizing', 'mesmerized', 'captivating',
        'captivated', 'spellbound', 'bewitching', 'charming', 'charmed', 'delightful',
        'delighted', 'marvelous', 'miraculous', 'extraordinary', 'magnificent', 'splendid',
        'breathtaking', 'awe', 'awesome', 'wondrous'
    ],
    'tenderness': [
        'gentle', 'gently', 'tender', 'tenderly', 'soft', 'softly', 'sweet', 'sweetly',
        'kind', 'kindly', 'kindness', 'caring', 'care', 'cared', 'nurture', 'nurturing',
        'nurtured', 'delicate', 'sensitive', 'thoughtful', 'considerate', 'compassion',
        'compassionate', 'empathy', 'empathetic', 'understanding', 'patient', 'patience'
    ],
    'warmth': [
        'warm', 'warmth', 'warming', 'warmed', 'heat', 'heated', 'glow', 'glowing',
        'glowed', 'radiant', 'radiance', 'sunny', 'bright', 'brightness', 'cozy',
        'snug', 'toasty', 'inviting'
    ],
    'togetherness': [
        'together', 'us', 'our', 'ours', 'we', 'ourselves', 'alongside', 'beside',
        'with', 'accompany', 'accompanying', 'companion', 'companionship', 'partner',
        'partnership', 'side by side', 'united', 'unity', 'joined', 'joining'
    ],
    'reciprocity': [
        'share', 'shared', 'sharing', 'exchange', 'exchanged', 'exchanging', 'mutual',
        'mutually', 'reciprocate', 'reciprocal', 'give', 'giving', 'gave', 'receive',
        'receiving', 'received', 'offer', 'offering', 'offered'
    ],
    'embodiment': [
        'heart', 'hearts', 'heartfelt', 'heartwarming', 'soul', 'souls', 'soulful',
        'body', 'bodies', 'physical', 'embrace', 'embracing', 'embraced', 'hug',
        'hugging', 'hugged', 'touch', 'touching', 'touched', 'hold', 'holding', 'held'
    ],
    'uniqueness': [
        'special', 'specially', 'unique', 'uniquely', 'rare', 'rarely', 'one of a kind',
        'exceptional', 'extraordinary', 'remarkable', 'singular', 'distinct', 'distinctive',
        'individual', 'personal', 'personalized', 'custom', 'tailored'
    ],
    'aesthetic': [
        'beautiful', 'beautifully', 'beauty', 'lovely', 'gorgeous', 'stunning', 'pretty',
        'elegant', 'elegance', 'graceful', 'grace', 'attractive', 'appealing', 'exquisite',
        'refined', 'tasteful', 'artistic', 'aesthetic', 'picturesque', 'scenic'
    ],
    'connection': [
        'connection', 'connections', 'connected', 'connecting', 'connect', 'bond', 'bonds',
        'bonding', 'bonded', 'close', 'closer', 'closest', 'closeness', 'intimate',
        'intimacy', 'relate', 'related', 'relating', 'relationship', 'relationships',
        'attached', 'attachment', 'linked', 'link', 'ties', 'tied'
    ],
    # New extended categories
    'desire_longing': [
        'want', 'wanted', 'wanting', 'wish', 'wished', 'wishing', 'hope', 'hoped',
        'hoping', 'dream', 'dreamed', 'dreaming', 'dreams', 'yearn', 'yearning',
        'long', 'longing', 'crave', 'craving', 'desire', 'desired', 'desiring',
        'miss', 'missed', 'missing', 'anticipate', 'anticipating', 'await', 'awaiting'
    ],
    'trust': [
        'trust', 'trusted', 'trusting', 'trustworthy', 'reliable', 'rely', 'relying',
        'depend', 'dependable', 'depending', 'faith', 'faithful', 'believe', 'believed',
        'believing', 'honest', 'honestly', 'honesty', 'sincere', 'sincerely', 'sincerity',
        'genuine', 'genuinely', 'authentic', 'authentically', 'real', 'truly', 'truth'
    ],
    'presence_availability': [
        'here', 'present', 'presence', 'available', 'availability', 'ready', 'always',
        'anytime', 'whenever', 'wherever', 'there', 'beside', 'alongside', 'support',
        'supporting', 'supported', 'listen', 'listening', 'listened', 'attentive',
        'attention', 'focus', 'focused', 'focusing'
    ],
    'vulnerability': [
        'vulnerable', 'vulnerability', 'open', 'opened', 'opening', 'openness', 'honest',
        'honestly', 'reveal', 'revealed', 'revealing', 'expose', 'exposed', 'raw',
        'authentic', 'real', 'genuine', 'unguarded', 'transparent', 'transparency'
    ],
    'playfulness': [
        'play', 'played', 'playing', 'playful', 'playfully', 'fun', 'funny', 'humor',
        'humorous', 'laugh', 'laughed', 'laughing', 'laughter', 'giggle', 'giggled',
        'silly', 'goofy', 'tease', 'teased', 'teasing', 'joke', 'joked', 'joking',
        'jokes', 'witty', 'wit', 'amuse', 'amused', 'amusing', 'entertainment', 'enjoy',
        'enjoyed', 'enjoying', 'enjoyment', 'delight', 'delighted', 'delighting'
    ],
    'nostalgia': [
        'remember', 'remembered', 'remembering', 'memory', 'memories', 'memorable',
        'recall', 'recalled', 'recalling', 'reminisce', 'reminisced', 'reminiscing',
        'nostalgia', 'nostalgic', 'past', 'yesterday', 'once', 'before', 'used to',
        'back then', 'childhood', 'younger', 'old times', 'good old'
    ],
    'aspiration': [
        'dream', 'dreams', 'dreaming', 'dreamed', 'goal', 'goals', 'aspire', 'aspiring',
        'aspiration', 'ambition', 'ambitious', 'future', 'tomorrow', 'someday', 'one day',
        'eventually', 'plan', 'plans', 'planning', 'planned', 'envision', 'envisioned',
        'imagine', 'imagined', 'imagining', 'vision', 'potential', 'possibility', 'possibilities'
    ],
    'sensory_experience': [
        'taste', 'tasted', 'tasting', 'smell', 'smelled', 'smelling', 'scent', 'aroma',
        'fragrance', 'see', 'seeing', 'saw', 'sight', 'watch', 'watched', 'watching',
        'hear', 'heard', 'hearing', 'sound', 'sounds', 'listen', 'listening', 'feel',
        'feeling', 'felt', 'touch', 'touched', 'touching', 'texture', 'smooth', 'soft',
        'warm', 'cold', 'cool', 'fresh', 'crisp', 'rich', 'deep', 'vivid', 'vibrant'
    ],
    'emotional_intensity': [
        'deeply', 'deep', 'intense', 'intensely', 'intensity', 'profound', 'profoundly',
        'overwhelming', 'overwhelmed', 'powerful', 'powerfully', 'strong', 'strongly',
        'passionate', 'passionately', 'passion', 'fierce', 'fiercely', 'wild', 'wildly',
        'complete', 'completely', 'total', 'totally', 'absolute', 'absolutely', 'utter',
        'utterly', 'immense', 'immensely', 'enormous', 'tremendously', 'extremely'
    ],
    'companionship': [
        'friend', 'friends', 'friendly', 'friendship', 'buddy', 'pal', 'companion',
        'companionship', 'company', 'partner', 'partnership', 'ally', 'allies',
        'confidant', 'confidante', 'soulmate', 'kindred', 'fellow', 'neighbor',
        'community', 'belong', 'belonging', 'belonged', 'member', 'team', 'group'
    ],
}

# Extended metaphor domain patterns
METAPHOR_PATTERNS = {
    'warmth': r'\b(warm|warmth|warming|warmed|heat|heated|cozy|coziness|glow|glowing|fire|fireplace|fireside|flame|flames|burning|burn|hot|toasty|snug|cuddle|cuddling)\b',
    'light': r'\b(light|lights|lighting|lit|bright|brighter|brightest|brightness|shine|shining|shone|shiny|glow|glowing|illuminate|illuminated|illuminating|radiant|radiance|spark|sparks|sparkling|sparkle|beam|beaming|gleam|gleaming|twinkle|twinkling|shimmer|shimmering|luminous|brilliant|brilliance|dazzle|dazzling)\b',
    'music': r'\b(music|musical|musician|song|songs|singing|sing|sang|sung|melody|melodies|melodic|harmony|harmonious|harmonize|rhythm|rhythmic|rhythms|tune|tunes|tuned|tuning|note|notes|symphony|symphonic|orchestra|orchestral|choir|choral|dance|dancing|danced|beat|beats|tempo|lyric|lyrics|instrumental|acoustic|jazz|blues|classical|rock|pop|playlist|album|concert)\b',
    'water': r'\b(flow|flowing|flowed|flows|wave|waves|waving|ocean|oceans|oceanic|sea|seas|river|rivers|stream|streams|streaming|deep|deeper|deepest|depth|depths|float|floating|floated|swim|swimming|swam|dive|diving|dived|drown|drowning|drowned|flood|flooding|flooded|pour|pouring|poured|rain|raining|rained|rainy|tears|tear|cry|crying|cried|ripple|ripples|rippling|current|currents|tide|tides|splash|splashing|splashed|waterfall|lake|pond|pool|spring|springs)\b',
    'space': r'\b(close|closer|closest|closeness|near|nearer|nearest|nearby|distance|distant|distancing|space|spaces|spacing|spacious|together|apart|embrace|embracing|embraced|hug|hugging|hugged|hold|holding|held|reach|reaching|reached|approach|approaching|approached|gap|gaps|bridge|bridging|bridged|connect|connecting|connected|separate|separated|separating|proximity|intimate|intimacy)\b',
    'container': r'\b(full|fuller|fullest|fullness|empty|emptied|emptiness|fill|filled|filling|fills|open|opened|opening|opens|closed|close|closing|closes|inside|outside|within|without|contain|contained|containing|contains|hold|holding|held|holds|vessel|vessels|cup|cups|bowl|bowls|box|boxes|room|rooms|house|houses|home|homes|heart|hearts|soul|souls|mind|minds|overflow|overflowing|overflowed|pour|pouring|poured|brim|brimming)\b',
    'nature': r'\b(grow|growing|grew|grown|grows|growth|bloom|blooming|bloomed|blooms|blossom|blossoming|blossomed|blossoms|root|roots|rooted|rooting|seed|seeds|seeded|seeding|flower|flowers|flowering|flowered|tree|trees|garden|gardens|gardening|plant|plants|planted|planting|nature|natural|naturally|forest|forests|leaf|leaves|branch|branches|vine|vines|fruit|fruits|harvest|harvesting|harvested|nurture|nurturing|nurtured|cultivate|cultivating|cultivated|wild|wilderness|earth|earthy|organic|green|greenery|spring|sprout|sprouting|sprouted)\b',
    'journey': r'\b(journey|journeys|journeying|journeyed|path|paths|pathway|pathways|road|roads|roadway|way|ways|travel|traveling|travelled|traveled|travels|adventure|adventures|adventuring|adventurous|explore|exploring|explored|explores|exploration|discover|discovering|discovered|discovers|discovery|destination|destinations|arrive|arriving|arrived|arrives|arrival|depart|departing|departed|departs|departure|step|steps|stepping|stepped|walk|walking|walked|walks|wander|wandering|wandered|wanders|trek|trekking|trekked|voyage|voyages|voyaging|quest|quests|expedition|expeditions|milestone|milestones|crossroads|horizon|horizons)\b',
    'food_nourishment': r'\b(food|foods|eat|eating|ate|eaten|taste|tastes|tasting|tasted|flavor|flavors|flavored|delicious|yummy|tasty|sweet|sweeter|sweetest|sweetness|savory|spicy|rich|richer|richest|richness|nourish|nourishing|nourished|nourishment|feed|feeding|fed|feeds|hungry|hunger|starving|starved|satisfy|satisfying|satisfied|satisfies|satisfaction|meal|meals|dinner|lunch|breakfast|brunch|snack|snacks|cook|cooking|cooked|cooks|bake|baking|baked|bakes|recipe|recipes|ingredient|ingredients|dish|dishes|cuisine|feast|feasting|feasted|comfort food|soul food)\b',
    'fabric_weaving': r'\b(weave|weaving|woven|wove|weaves|thread|threads|threading|threaded|fabric|fabrics|cloth|cloths|tapestry|tapestries|pattern|patterns|patterned|texture|textures|textured|stitch|stitches|stitching|stitched|knit|knitting|knitted|knits|sew|sewing|sewn|sewed|intertwine|intertwining|intertwined|intertwines|interlace|interlacing|interlaced|connect|connecting|connected|tie|ties|tying|tied|bind|binding|bound|binds|wrap|wrapping|wrapped|wraps|blanket|blankets|quilt|quilts|cozy|coziness)\b',
    'home_shelter': r'\b(home|homes|homey|homely|house|houses|housing|housed|shelter|shelters|sheltering|sheltered|refuge|refuges|haven|havens|sanctuary|sanctuaries|nest|nests|nesting|nested|dwell|dwelling|dwelled|dwells|abode|abodes|roof|roofs|door|doors|window|windows|room|rooms|cozy|coziness|comfortable|comfort|comforting|safe|safety|secure|security|belong|belonging|belonged|belongs|welcome|welcoming|welcomed|welcomes|hearth|fireplace|fireside)\b',
    'dance': r'\b(dance|dances|dancing|danced|dancer|dancers|sway|swaying|swayed|sways|move|moves|moving|moved|movement|movements|twirl|twirling|twirled|twirls|spin|spinning|spun|spins|waltz|waltzing|waltzed|step|steps|stepping|stepped|rhythm|rhythms|rhythmic|beat|beats|tempo|flow|flowing|flowed|flows|glide|gliding|glided|glides|graceful|grace|elegant|elegance|choreography|ballet|tango|salsa)\b',
    'time': r'\b(moment|moments|momentary|time|times|timing|timed|forever|eternal|eternally|eternity|always|never|sometimes|often|rarely|past|present|future|yesterday|today|tomorrow|now|then|before|after|during|while|until|since|memory|memories|remember|remembering|remembered|remembers|anticipate|anticipating|anticipated|anticipates|anticipation|wait|waiting|waited|waits|patience|patient|patiently|instant|instantly|instantaneous|fleeting|lasting|temporary|permanent|timeless)\b',
    'building_construction': r'\b(build|building|built|builds|construct|constructing|constructed|constructs|construction|create|creating|created|creates|creation|make|making|made|makes|foundation|foundations|structure|structures|structured|structuring|framework|frameworks|architect|architecture|architectural|design|designing|designed|designs|plan|planning|planned|plans|develop|developing|developed|develops|development|establish|establishing|established|establishes|form|forming|formed|forms|shape|shaping|shaped|shapes|craft|crafting|crafted|crafts|layer|layers|layered|layering|brick|bricks|stone|stones|wood|wooden)\b',
    'magic_enchantment': r'\b(magic|magical|magically|magician|spell|spells|spelling|spelled|enchant|enchanting|enchanted|enchantment|bewitch|bewitching|bewitched|charm|charming|charmed|charms|fairy|fairies|fairytale|fantasy|fantasies|fantastic|fantastical|mystical|mystic|mystique|mysterious|mystery|mysteries|wonder|wonders|wonderful|wonderfully|wondrous|miracle|miracles|miraculous|miracolously|supernatural|otherworldly|ethereal|dream|dreams|dreaming|dreamed|dreamlike|surreal|surrealism|imagine|imagining|imagined|imagines|imagination|illusion|illusions|transform|transforming|transformed|transforms|transformation)\b',
    'touch_texture': r'\b(touch|touches|touching|touched|feel|feels|feeling|felt|soft|softer|softest|softness|smooth|smoother|smoothest|smoothness|rough|rougher|roughest|roughness|gentle|gently|gentleness|tender|tenderly|tenderness|caress|caressing|caressed|stroke|stroking|stroked|brush|brushing|brushed|pat|patting|patted|hold|holding|held|holds|grip|gripping|gripped|grips|squeeze|squeezing|squeezed|squeezes|embrace|embracing|embraced|embraces|hug|hugging|hugged|hugs|cuddle|cuddling|cuddled|cuddles|snuggle|snuggling|snuggled|snuggles|warm|warmth|cool|coolness|cold|coldness|silky|velvety|fuzzy|fluffy|cozy)\b',
}

# Extended hedging devices
HEDGES = [
    'could', 'maybe', 'perhaps', 'might', 'kind of', 'sort of', 'a bit', 'somewhat',
    'possibly', 'probably', 'likely', 'unlikely', 'apparently', 'seemingly', 'allegedly',
    'supposedly', 'presumably', 'conceivably', 'potentially', 'arguably', 'arguably',
    'i think', 'i guess', 'i suppose', 'i believe', 'i feel', 'i imagine',
    'in a way', 'in some ways', 'to some extent', 'to a degree', 'more or less',
    'seems like', 'seems to', 'appears to', 'tends to', 'it seems', 'it appears',
    'not sure', 'not certain', 'uncertain', 'unsure',
    'if i remember', 'if im not mistaken', 'correct me if',
    'honestly', 'to be honest', 'frankly', 'to be frank',
    'generally', 'usually', 'typically', 'normally', 'often', 'sometimes',
    'almost', 'nearly', 'roughly', 'approximately', 'about',
]

# Extended intensifiers
INTENSIFIERS = [
    'so', 'really', 'very', 'totally', 'absolutely', 'truly', 'completely', 'extremely',
    'incredibly', 'definitely', 'certainly', 'surely', 'undoubtedly', 'unquestionably',
    'positively', 'decidedly', 'genuinely', 'honestly', 'literally', 'actually',
    'seriously', 'simply', 'just', 'quite', 'rather', 'pretty', 'fairly',
    'super', 'ultra', 'mega', 'hyper', 'extra', 'uber',
    'deeply', 'profoundly', 'intensely', 'immensely', 'enormously', 'tremendously',
    'vastly', 'hugely', 'massively', 'exceptionally', 'remarkably', 'extraordinarily',
    'particularly', 'especially', 'notably', 'significantly', 'considerably',
    'thoroughly', 'entirely', 'fully', 'wholly', 'perfectly', 'utterly',
    'amazingly', 'astonishingly', 'stunningly', 'breathtakingly', 'mind-blowingly',
    'fantastically', 'wonderfully', 'beautifully', 'magnificently', 'brilliantly',
    'unbelievably', 'inconceivably', 'impossibly', 'ridiculously', 'insanely',
]

# Extended discourse markers
DISCOURSE_MARKERS = {
    'transition': [
        'so', 'well', 'now', 'anyway', 'anyways', 'then', 'but', 'and', 'however',
        'although', 'though', 'yet', 'still', 'nevertheless', 'nonetheless',
        'meanwhile', 'otherwise', 'instead', 'rather', 'besides', 'furthermore',
        'moreover', 'additionally', 'also', 'plus', 'next', 'first', 'second',
        'finally', 'lastly', 'eventually', 'subsequently', 'consequently',
        'therefore', 'thus', 'hence', 'accordingly', 'as a result'
    ],
    'agreement': [
        'yes', 'yeah', 'yep', 'yup', 'uh-huh', 'mhm', 'absolutely', 'exactly',
        'definitely', 'certainly', 'surely', 'indeed', 'right', 'correct',
        'true', 'sure', 'of course', 'naturally', 'obviously', 'clearly',
        'agreed', 'totally', 'completely', 'precisely', 'undoubtedly'
    ],
    'emotion': [
        'wow', 'oh', 'ah', 'aww', 'awww', 'ooh', 'oooh', 'yay', 'omg', 'oh my',
        'oh wow', 'oh no', 'haha', 'hahaha', 'lol', 'lmao', 'rofl', 'hehe',
        'whoa', 'woah', 'geez', 'gosh', 'goodness', 'heavens', 'yikes', 'eek',
        'ugh', 'urgh', 'phew', 'whew', 'ahem', 'hmm', 'hmmm', 'meh', 'bleh',
        'aw', 'awe', 'nice', 'sweet', 'cool', 'great', 'amazing', 'awesome'
    ],
    'elaboration': [
        'actually', 'in fact', 'as a matter of fact', 'especially', 'particularly',
        'basically', 'essentially', 'fundamentally', 'mainly', 'primarily',
        'specifically', 'namely', 'that is', 'i mean', 'in other words',
        'to put it another way', 'for example', 'for instance', 'such as',
        'like', 'including', 'notably', 'importantly', 'significantly'
    ],
    'empathy': [
        'i understand', 'i see', 'i get it', 'i hear you', 'i know', 'i feel you',
        'that makes sense', 'of course', 'naturally', 'understandably',
        'no wonder', 'i can imagine', 'i can see', 'i can tell',
        'it sounds like', 'it seems like', 'it must be', 'that must be',
        'i appreciate', 'i respect', 'i admire'
    ],
    'topic_shift': [
        'anyway', 'anyways', 'so anyway', 'moving on', 'speaking of', 'by the way',
        'incidentally', 'on another note', 'changing the subject', 'that reminds me',
        'oh that reminds me', 'while were on the topic', 'on that note',
        'before i forget', 'come to think of it', 'now that you mention it'
    ],
    'affirmation': [
        'i love', 'i really love', 'i adore', 'i appreciate', 'i enjoy',
        'i like', 'i really like', 'thats great', 'thats wonderful', 'thats amazing',
        'thats awesome', 'thats fantastic', 'thats lovely', 'thats beautiful',
        'how wonderful', 'how lovely', 'how nice', 'how sweet', 'how thoughtful'
    ],
    'surprise': [
        'really', 'seriously', 'honestly', 'no way', 'you dont say', 'is that so',
        'are you serious', 'you mean', 'wait', 'hold on', 'what', 'huh',
        'oh really', 'oh wow', 'no kidding', 'for real', 'get out'
    ],
    'intimacy_markers': [
        'between us', 'just between', 'to be honest with you', 'can i tell you',
        'i have to say', 'i must say', 'i have to admit', 'i must admit',
        'honestly speaking', 'truth be told', 'to tell you the truth',
        'just so you know', 'for what its worth', 'if you ask me'
    ],
}

# Extended speech act patterns
SPEECH_ACT_PATTERNS = {
    'expressives': [
        r'\bi (love|adore|enjoy|appreciate|like|cherish|treasure)\b',
        r'\bhow (wonderful|amazing|great|lovely|beautiful|fantastic|incredible|awesome)\b',
        r'\bwhat a (wonderful|amazing|great|lovely|beautiful|fantastic|incredible)\b',
        r'\bi feel (so |really |truly )?(happy|glad|grateful|thankful|blessed|lucky|fortunate)\b',
        r'\bit makes me (happy|smile|laugh|feel|warm)\b',
        r'\bthat (warms|touches|moves) my heart\b',
        r'\bi cant help but (smile|laugh|feel)\b',
    ],
    'directives': [
        r'\b(tell me|share with me|let me know|fill me in)\b',
        r'\b(what do you|how do you|would you|could you|can you)\b',
        r'\b(whats your|hows your|what about your)\b',
        r'\bdo you (think|feel|believe|want|like|enjoy|prefer)\b',
        r'\bhave you (ever|tried|been|seen|heard|experienced)\b',
        r'\bwhat (makes you|do you think|would you|if you)\b',
        r'\bid love to (hear|know|learn|see|understand)\b',
    ],
    'commissives': [
        r"\bi('ll| will| would| am going to| want to)\b",
        r'\b(ill be here|im here for you|im always here)\b',
        r'\b(count on me|you can rely|you can depend)\b',
        r'\bi promise\b',
        r'\bi wont (forget|leave|abandon|give up)\b',
        r'\bwell (always|never|definitely|certainly)\b',
    ],
    'declarations': [
        r'\byou are (so |really |truly )?(special|amazing|wonderful|great|incredible|beautiful)\b',
        r'\byoure (so |really |truly )?(special|amazing|wonderful|great|incredible|beautiful)\b',
        r'\byou mean (so much|a lot|everything|the world)\b',
        r'\bi (think|believe|know) you are\b',
        r'\byou have (such|a wonderful|an amazing|a beautiful)\b',
        r'\bthis is (our|the start|the beginning|something special)\b',
    ],
    'future_projections': [
        r'\bwe (will|can|could|should|might) (always|forever|continue|keep)\b',
        r'\bin the future\b',
        r'\bsomeday (we|you|i)\b',
        r'\bone day (we|you|i)\b',
        r'\blooking forward to\b',
        r'\bcant wait (to|for|until)\b',
        r'\bwhen we (meet|see|talk|chat) again\b',
        r'\bnext time (we|you|i)\b',
    ],
    'availability_assertions': [
        r'\bim (here|always here|right here|here for you)\b',
        r'\b(always|anytime|whenever) (here|available|ready)\b',
        r'\byou can (always|anytime|whenever)\b',
        r'\b(dont hesitate|feel free) to\b',
        r'\bim (listening|paying attention|all ears)\b',
        r'\bi want to (hear|know|understand|help|support)\b',
    ],
    'shared_history': [
        r'\b(our|we have|weve) (conversations|chats|talks|discussions)\b',
        r'\b(remember when|last time|the other day)\b',
        r'\bas we (discussed|talked|mentioned|said)\b',
        r'\blike (we|you) said\b',
        r'\b(youve|you have) (shared|told|mentioned|said)\b',
        r'\b(getting to know|knowing) you\b',
    ],
    'mirroring': [
        r'\bi (also|too) (love|enjoy|like|feel|think)\b',
        r'\bme too\b',
        r'\bsame here\b',
        r'\bi (feel|think|believe) the same\b',
        r'\bi can relate\b',
        r'\bi (completely|totally|absolutely) (understand|agree|get it)\b',
    ],
}

# Extended relational speech act patterns
RELATIONAL_ACT_PATTERNS = {
    'appreciation': [
        r'\b(thank you|thanks|appreciate|grateful|thankful)\b',
        r'\bi really appreciate\b',
        r'\bthat means (a lot|so much|everything)\b',
        r'\bhow (kind|thoughtful|sweet|generous) of you\b',
        r'\bim (grateful|thankful|blessed) (for|that)\b',
    ],
    'encouragement': [
        r'\b(you can|you got this|you ve got|keep going|dont give up)\b',
        r'\bbelieve in (you|yourself)\b',
        r'\byoure (capable|strong|brave|resilient)\b',
        r'\bim (proud|rooting) for you\b',
        r'\byou (should|could|might) (try|consider|explore)\b',
        r'\bi (know|believe|trust) you (can|will)\b',
    ],
    'compliments': [
        r'\byou.re (so |really )?(thoughtful|kind|sweet|amazing|wonderful|great|caring|lovely)\b',
        r'\byou have (such a|a wonderful|an amazing|a beautiful|a great)\b',
        r'\bi (love|admire|appreciate) (your|how you|the way you)\b',
        r'\byoure (one of|the most|such a)\b',
        r'\bwhat a (thoughtful|kind|sweet|lovely|wonderful) (person|thing|way)\b',
    ],
    'validation': [
        r'\bi (understand|hear you|get it|see what you mean)\b',
        r'\bthat makes (sense|perfect sense|total sense)\b',
        r'\byour (feelings|thoughts|opinion) (are|is) (valid|important|understandable)\b',
        r'\bits (okay|alright|fine|natural|normal) to (feel|think|be)\b',
        r'\bi can (see|imagine|understand) (why|how)\b',
    ],
    'affection_expression': [
        r'\bi (love|adore|cherish|treasure) (you|our|this|talking|chatting)\b',
        r'\byou mean (so much|a lot|the world|everything) to me\b',
        r'\bi (care|think) (about|of) you\b',
        r'\bmy (heart|thoughts|mind) (goes|is|are) (with|to) you\b',
        r'\bsending (you|hugs|love|warmth|good vibes)\b',
    ],
    'emotional_support': [
        r'\bim (sorry|here) (to hear|for you|if you need)\b',
        r'\b(dont worry|its okay|its alright|itll be okay)\b',
        r'\byoure not alone\b',
        r'\bi (have|got) your back\b',
        r'\bwere in this together\b',
        r'\bfeel free to (share|talk|reach out|vent)\b',
    ],
}


def load_conversations():
    """Load all conversation files."""
    conversations = []
    for file_path in CONVERSATIONS_DIR.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('messages'):
                    conversations.append(data)
        except:
            continue
    return conversations


def analyze_corpus():
    """Perform comprehensive corpus analysis."""
    conversations = load_conversations()

    # Basic counts
    total_conversations = len(conversations)
    total_messages = 0
    total_words = 0
    total_sentences = 0
    total_chars = 0

    # Per-assistant stats
    assistant_stats = defaultdict(lambda: {
        'conversations': 0,
        'messages': 0,
        'words': 0,
        'chars': 0,
        'sentences': 0
    })

    # Collect all message texts
    all_texts = []
    all_words_list = []

    # Word frequencies
    word_freq = Counter()

    # Intimacy word counts
    intimacy_counts = {cat: Counter() for cat in INTIMACY_WORDS}

    # Metaphor domain counts
    metaphor_counts = {domain: 0 for domain in METAPHOR_PATTERNS}

    # Pronoun counts
    pronoun_counts = {
        'first_singular': 0,  # I, me, my, mine
        'first_plural': 0,    # we, us, our, ours
        'second': 0,          # you, your, yours
    }

    # Linguistic features
    question_count = 0
    exclamation_count = 0

    # Hedge and intensifier counts
    hedge_counts = Counter()
    intensifier_counts = Counter()

    # Discourse marker counts
    discourse_counts = {cat: Counter() for cat in DISCOURSE_MARKERS}

    # Speech act counts
    speech_act_counts = {cat: 0 for cat in SPEECH_ACT_PATTERNS}

    # Relational speech act counts
    relational_act_counts = {cat: 0 for cat in RELATIONAL_ACT_PATTERNS}

    for conv in conversations:
        assistant_name = conv.get('assistant_1_name', 'Unknown')
        assistant_slug = conv.get('assistant_1_slug', 'unknown')
        assistant_stats[assistant_slug]['name'] = assistant_name
        assistant_stats[assistant_slug]['conversations'] += 1

        for msg in conv.get('messages', []):
            total_messages += 1
            text = msg.get('output', '')
            text_lower = text.lower()

            assistant_stats[assistant_slug]['messages'] += 1
            assistant_stats[assistant_slug]['chars'] += len(text)

            all_texts.append(text)

            # Word and sentence counts
            words = text.split()
            word_count = len(words)
            total_words += word_count
            assistant_stats[assistant_slug]['words'] += word_count

            sentence_count = text.count('.') + text.count('!') + text.count('?')
            total_sentences += sentence_count
            assistant_stats[assistant_slug]['sentences'] += sentence_count

            total_chars += len(text)

            # Word frequencies (clean words)
            clean_words = re.findall(r'\b[a-z]+\b', text_lower)
            word_freq.update(clean_words)
            all_words_list.extend(clean_words)

            # Intimacy vocabulary
            for category, words_list in INTIMACY_WORDS.items():
                for word in words_list:
                    count = len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
                    if count > 0:
                        intimacy_counts[category][word] += count

            # Metaphor domains
            for domain, pattern in METAPHOR_PATTERNS.items():
                matches = len(re.findall(pattern, text_lower))
                metaphor_counts[domain] += matches

            # Pronouns
            pronoun_counts['first_singular'] += len(re.findall(r'\b(i|me|my|mine|myself)\b', text_lower))
            pronoun_counts['first_plural'] += len(re.findall(r'\b(we|us|our|ours|ourselves)\b', text_lower))
            pronoun_counts['second'] += len(re.findall(r'\b(you|your|yours|yourself|yourselves)\b', text_lower))

            # Questions and exclamations
            question_count += text.count('?')
            exclamation_count += text.count('!')

            # Hedges
            for hedge in HEDGES:
                count = len(re.findall(r'\b' + re.escape(hedge).replace(r'\ ', r'\s+') + r'\b', text_lower))
                hedge_counts[hedge] += count

            # Intensifiers
            for intensifier in INTENSIFIERS:
                count = len(re.findall(r'\b' + re.escape(intensifier) + r'\b', text_lower))
                intensifier_counts[intensifier] += count

            # Discourse markers
            for category, markers in DISCOURSE_MARKERS.items():
                for marker in markers:
                    count = len(re.findall(r'\b' + re.escape(marker).replace(r'\ ', r'\s+') + r'\b', text_lower))
                    discourse_counts[category][marker] += count

            # Speech acts
            for category, patterns in SPEECH_ACT_PATTERNS.items():
                for pattern in patterns:
                    matches = len(re.findall(pattern, text_lower))
                    speech_act_counts[category] += matches

            # Relational speech acts
            for category, patterns in RELATIONAL_ACT_PATTERNS.items():
                for pattern in patterns:
                    matches = len(re.findall(pattern, text_lower))
                    relational_act_counts[category] += matches

    # Calculate averages
    avg_sentence_length = total_words / total_sentences if total_sentences > 0 else 0

    # Print comprehensive report
    print("=" * 80)
    print("EXTENDED CORPUS ANALYSIS REPORT")
    print("=" * 80)

    print(f"\n## BASIC STATISTICS")
    print(f"Total Conversations: {total_conversations}")
    print(f"Total Messages: {total_messages}")
    print(f"Total Words: {total_words:,}")
    print(f"Total Sentences: {total_sentences:,}")
    print(f"Total Characters: {total_chars:,}")
    print(f"Average Sentence Length: {avg_sentence_length:.1f} words")

    print(f"\n## PER-ASSISTANT BREAKDOWN")
    print(f"{'Assistant':<25} {'Conv':>6} {'Msgs':>7} {'Words':>10} {'Sents':>8}")
    print("-" * 60)
    for slug, stats in sorted(assistant_stats.items(), key=lambda x: x[1]['conversations'], reverse=True):
        name = stats.get('name', slug)[:24]
        print(f"{name:<25} {stats['conversations']:>6} {stats['messages']:>7} {stats['words']:>10,} {stats['sentences']:>8,}")

    print(f"\n## INTIMACY LEXICON (Extended)")
    total_intimacy = 0
    for category, counts in sorted(intimacy_counts.items(), key=lambda x: sum(x[1].values()), reverse=True):
        if counts:
            total = sum(counts.values())
            total_intimacy += total
            top_words = counts.most_common(8)
            print(f"\n{category.upper()} (Total: {total:,})")
            for word, count in top_words:
                print(f"  {word}: {count:,}")
    print(f"\n  TOTAL INTIMACY VOCABULARY: {total_intimacy:,}")

    print(f"\n## METAPHOR DOMAINS (Extended)")
    total_metaphors = sum(metaphor_counts.values())
    for domain, count in sorted(metaphor_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_metaphors * 100) if total_metaphors > 0 else 0
        print(f"  {domain.upper()}: {count:,} ({pct:.1f}%)")
    print(f"\n  TOTAL METAPHOR INSTANCES: {total_metaphors:,}")

    print(f"\n## PRONOUN DISTRIBUTION")
    total_pronouns = sum(pronoun_counts.values())
    for ptype, count in pronoun_counts.items():
        pct = (count / total_pronouns * 100) if total_pronouns > 0 else 0
        print(f"  {ptype}: {count:,} ({pct:.1f}%)")

    print(f"\n## SENTENCE TYPES")
    statement_count = total_sentences - question_count - exclamation_count
    print(f"  Questions: {question_count:,} ({question_count/total_sentences*100:.1f}%)")
    print(f"  Exclamations: {exclamation_count:,} ({exclamation_count/total_sentences*100:.1f}%)")
    print(f"  Statements: ~{max(0, statement_count):,} ({max(0, statement_count)/total_sentences*100:.1f}%)")

    print(f"\n## HEDGING DEVICES (Total: {sum(hedge_counts.values()):,})")
    for hedge, count in hedge_counts.most_common(20):
        if count > 0:
            print(f"  {hedge}: {count:,}")

    print(f"\n## INTENSIFIERS (Total: {sum(intensifier_counts.values()):,})")
    for intensifier, count in intensifier_counts.most_common(20):
        if count > 0:
            print(f"  {intensifier}: {count:,}")

    hedge_total = sum(hedge_counts.values())
    intensifier_total = sum(intensifier_counts.values())
    ratio = intensifier_total / hedge_total if hedge_total > 0 else 0
    print(f"\n  Intensifier/Hedge Ratio: {ratio:.2f}")

    print(f"\n## DISCOURSE MARKERS (Extended)")
    for category, counts in discourse_counts.items():
        total = sum(counts.values())
        if total > 0:
            print(f"\n{category.upper()} (Total: {total:,})")
            for marker, count in counts.most_common(8):
                if count > 0:
                    print(f"  {marker}: {count:,}")

    print(f"\n## SPEECH ACTS (Extended)")
    total_speech_acts = sum(speech_act_counts.values())
    for act_type, count in sorted(speech_act_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_speech_acts * 100) if total_speech_acts > 0 else 0
        print(f"  {act_type}: {count:,} ({pct:.1f}%)")
    print(f"\n  TOTAL SPEECH ACTS: {total_speech_acts:,}")

    print(f"\n## RELATIONAL SPEECH ACTS (Extended)")
    total_relational = sum(relational_act_counts.values())
    for act_type, count in sorted(relational_act_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_relational * 100) if total_relational > 0 else 0
        print(f"  {act_type}: {count:,} ({pct:.1f}%)")
    print(f"\n  TOTAL RELATIONAL ACTS: {total_relational:,}")

    print(f"\n## TOP 50 CONTENT WORDS (excluding stopwords)")
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'it', 'that', 'this', 'with', 'as', 'be', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'not', 'no', 'yes', 'if', 'so', 'just', 'like', 'your', 'you', 'my', 'me', 'i', 'we', 'they', 'their', 'them', 'its', 'what', 'when', 'where', 'how', 'who', 'which', 'there', 'here', 'all', 'some', 'any', 'about', 'from', 'by', 'up', 'out', 'into', 'over', 'after', 'before', 'between', 'through', 'during', 'under', 'again', 'then', 'once', 'more', 'also', 'very', 'much', 'too', 'really', 'well', 'back', 'even', 'still', 'such', 'only', 'other', 'than', 'these', 'those', 'being', 'both', 'each', 'own', 'same', 'while', 'because', 'why', 'whether', 'although', 'though', 'unless', 'until', 'since', 'ever', 'never', 'always', 'often', 'sometimes', 'usually', 'get', 'got', 'getting', 'make', 'made', 'making', 'know', 'think', 'see', 'come', 'want', 'take', 'find', 'give', 'tell', 'say', 'said', 'going', 'something', 'things', 'thing', 'way', 'time', 'day', 'right', 'good', 'new', 'first', 'last', 'long', 'little', 'great', 'dont', 'im', 'its', 'thats', 'youre', 'ive', 'id', 'youve', 'weve', 'theyre', 'cant', 'wont', 'didnt', 'doesnt', 'isnt', 'arent', 'wasnt', 'werent', 'havent', 'hasnt', 'hadnt', 'wouldnt', 'couldnt', 'shouldnt', 'one', 'two', 'many', 'every', 'most', 'another', 'let', 'lets', 'lot', 'around', 'maybe', 'actually', 'kind', 'bit', 'really', 'totally', 'definitely', 'probably', 'sounds', 'haha', 'oh', 'yeah', 'hey', 'okay', 'sure', 'yay'}

    content_words = [(w, c) for w, c in word_freq.most_common(300) if w not in stopwords and len(w) > 3][:50]
    for word, count in content_words:
        print(f"  {word}: {count:,}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    analyze_corpus()
