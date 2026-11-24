USE glowguide;

START TRANSACTION;

INSERT INTO products
(
    product_name,
    brand,
    category,
    description,
    skin_type,
    skin_concerns,
    ingredients,
    price,
    image_path,
    usage_instructions,
    is_active
)
VALUES

-- 3 CLEANSERS

(
    'Gentle Foaming Cleanser',
    'GlowGuide',
    'Cleanser',
    'A gentle foaming cleanser for everyday cleansing.',
    'oily, combination, normal',
    'excess oil, clogged pores',
    'glycerin, niacinamide',
    299.00,
    NULL,
    'Use daily with water.',
    1
),

(
    'Creamy Barrier Cleanser',
    'GlowGuide',
    'Cleanser',
    'A creamy cleanser designed for dry and sensitive skin.',
    'dry, sensitive, normal',
    'dryness, skin barrier support',
    'ceramides, glycerin, aloe vera',
    329.00,
    NULL,
    'Use daily with water.',
    1
),

(
    'Purifying Acne Cleanser',
    'GlowGuide',
    'Cleanser',
    'A cleanser formulated for skin prone to excess oil and breakouts.',
    'oily, combination',
    'acne, excess oil, clogged pores',
    'salicylic acid, tea tree',
    279.00,
    NULL,
    'Use as directed.',
    1
),

-- 4 TONERS

(
    'Hydrating Hyaluronic Toner',
    'GlowGuide',
    'Toner',
    'A lightweight hydrating toner for everyday skincare.',
    'dry, normal, combination',
    'dryness, dehydration',
    'hyaluronic acid, glycerin',
    349.00,
    NULL,
    'Apply after cleansing.',
    1
),

(
    'Balancing Niacinamide Toner',
    'GlowGuide',
    'Toner',
    'A balancing toner for skin with excess oil.',
    'oily, combination',
    'excess oil, uneven skin tone',
    'niacinamide, zinc',
    379.00,
    NULL,
    'Apply after cleansing.',
    1
),

(
    'Soothing Oat Toner',
    'GlowGuide',
    'Toner',
    'A gentle toner designed to soothe and hydrate the skin.',
    'sensitive, dry, normal',
    'redness, dryness',
    'oat extract, aloe vera, glycerin',
    329.00,
    NULL,
    'Apply after cleansing.',
    1
),

(
    'Clarifying Toner',
    'GlowGuide',
    'Toner',
    'A clarifying toner for oily and combination skin.',
    'oily, combination',
    'clogged pores, excess oil',
    'salicylic acid, niacinamide',
    399.00,
    NULL,
    'Use as directed.',
    1
),

-- 4 SERUMS

(
    'Niacinamide Serum',
    'GlowGuide',
    'Serum',
    'A lightweight serum for improving the appearance of uneven skin tone.',
    'oily, combination, normal',
    'excess oil, pigmentation',
    'niacinamide, zinc',
    449.00,
    NULL,
    'Use in the morning or evening.',
    1
),

(
    'Hyaluronic Hydration Serum',
    'GlowGuide',
    'Serum',
    'A hydrating serum designed to improve skin moisture.',
    'dry, normal, oily, combination',
    'dryness, dehydration',
    'hyaluronic acid, glycerin',
    499.00,
    NULL,
    'Use in the morning or evening.',
    1
),

(
    'Retinol Night Serum',
    'GlowGuide',
    'Serum',
    'A night serum formulated with retinol for an evening skincare routine.',
    'normal, oily, combination',
    'uneven texture, signs of ageing',
    'retinol, squalane',
    549.00,
    NULL,
    'Use at night. Start slowly and follow product directions. Use sunscreen during the day.',
    1
),

(
    'Calming Centella Serum',
    'GlowGuide',
    'Serum',
    'A calming serum designed for sensitive and irritated-looking skin.',
    'sensitive, dry, normal, combination',
    'redness, skin irritation',
    'centella asiatica, panthenol, glycerin',
    479.00,
    NULL,
    'Use in the morning or evening.',
    1
),

-- 2 MOISTURIZERS

(
    'Ceramide Repair Cream',
    'GlowGuide',
    'Moisturizer',
    'A nourishing moisturizer designed to support skin hydration.',
    'dry, sensitive, normal',
    'dryness, skin barrier support',
    'ceramides, glycerin, hyaluronic acid',
    429.00,
    NULL,
    'Apply after cleansing.',
    1
),

(
    'Lightweight Daily Lotion',
    'GlowGuide',
    'Moisturizer',
    'A lightweight daily moisturizer for comfortable hydration.',
    'oily, combination, normal',
    'dryness, excess oil',
    'glycerin, aloe vera, niacinamide',
    379.00,
    NULL,
    'Apply after cleansing.',
    1
),

-- 4 SUNSCREENS

(
    'Matte Finish Sunscreen SPF 50',
    'GlowGuide',
    'Sunscreen',
    'A lightweight sunscreen with a matte finish.',
    'oily, combination, normal',
    'sun protection, excess shine',
    'zinc oxide, niacinamide',
    499.00,
    NULL,
    'Apply before sun exposure. Reapply as directed.',
    1
),

(
    'Hydrating Sunscreen SPF 50',
    'GlowGuide',
    'Sunscreen',
    'A hydrating sunscreen for daily sun protection.',
    'dry, normal, combination',
    'sun protection, dryness',
    'zinc oxide, glycerin, vitamin e',
    529.00,
    NULL,
    'Apply before sun exposure. Reapply as directed.',
    1
),

(
    'Sensitive Skin Sunscreen SPF 50',
    'GlowGuide',
    'Sunscreen',
    'A gentle sunscreen formulated for sensitive skin.',
    'sensitive, dry, normal',
    'sun protection, skin sensitivity',
    'zinc oxide, aloe vera',
    549.00,
    NULL,
    'Apply before sun exposure. Reapply as directed.',
    1
),

(
    'Daily Lightweight Sunscreen SPF 30',
    'GlowGuide',
    'Sunscreen',
    'A lightweight sunscreen for everyday use.',
    'oily, combination, normal, dry',
    'sun protection',
    'zinc oxide, glycerin',
    399.00,
    NULL,
    'Apply before sun exposure. Reapply as directed.',
    1
);

COMMIT;
