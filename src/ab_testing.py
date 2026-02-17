"""
A/B Test Simulator Module.
Analyzes historical title patterns and thumbnail features to predict performance changes.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from io import BytesIO

try:
    from PIL import Image, ImageStat, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ABTestSimulator:
    """Simulate A/B tests based on historical title patterns."""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize with video data."""
        self.df = df.copy()
    
    def extract_title_features(self) -> pd.DataFrame:
        """Extract features from video titles."""
        features = []
        
        for _, row in self.df.iterrows():
            title = str(row.get('title', '')).lower()
            
            # Common patterns
            has_number = bool(re.search(r'\d+', title))
            has_howto = 'how to' in title or 'how-to' in title
            has_tips = 'tip' in title or 'tips' in title
            has_secrets = 'secret' in title or 'secrets' in title
            has_guide = 'guide' in title or 'tutorial' in title
            has_versus = 'vs' in title or 'versus' in title
            has_list = 'list' in title
            has_review = 'review' in title
            has_myth = 'myth' in title or 'false' in title
            has_why = 'why' in title
            has_best = 'best' in title
            has_beginner = 'beginner' in title or 'start' in title
            has_advanced = 'advanced' in title or 'pro' in title
            
            # Question detection
            has_question = '?' in title
            
            # Length
            title_length = len(title)
            word_count = len(title.split())
            
            features.append({
                'video_id': row.get('video_id'),
                'views': row.get('views', 0),
                'ctr': row.get('ctr', 0),
                'engagement_rate': row.get('engagement_rate', 0),
                'has_number': has_number,
                'has_howto': has_howto,
                'has_tips': has_tips,
                'has_secrets': has_secrets,
                'has_guide': has_guide,
                'has_versus': has_versus,
                'has_list': has_list,
                'has_review': has_review,
                'has_myth': has_myth,
                'has_why': has_why,
                'has_best': has_best,
                'has_beginner': has_beginner,
                'has_advanced': has_advanced,
                'has_question': has_question,
                'title_length': title_length,
                'word_count': word_count
            })
        
        return pd.DataFrame(features)
    
    def analyze_title_patterns(self) -> Dict:
        """Analyze which title patterns perform best."""
        features_df = self.extract_title_features()
        
        if features_df.empty:
            return {'error': 'No data available'}
        
        # Minimum sample size for reliable analysis
        min_sample_size = 3
        
        patterns = {}
        
        # Analyze each feature
        feature_cols = ['has_number', 'has_howto', 'has_tips', 'has_secrets', 
                       'has_guide', 'has_versus', 'has_list', 'has_review',
                       'has_myth', 'has_why', 'has_best', 'has_beginner', 
                       'has_advanced', 'has_question']
        
        for feature in feature_cols:
            if feature in features_df.columns:
                with_feature = features_df[features_df[feature] == True]
                without_feature = features_df[features_df[feature] == False]
                
                # Only analyze if we have enough samples
                if len(with_feature) >= min_sample_size and len(without_feature) >= min_sample_size:
                    avg_views_with = with_feature['views'].mean()
                    avg_views_without = without_feature['views'].mean()
                    
                    if avg_views_without > 0:
                        improvement = ((avg_views_with - avg_views_without) / avg_views_without) * 100
                        
                        # Cap improvement to realistic bounds (max ±30%)
                        improvement = max(-30, min(30, improvement))
                        
                        # Calculate confidence based on sample size
                        total_samples = len(with_feature) + len(without_feature)
                        if total_samples >= 20:
                            confidence = "High"
                        elif total_samples >= 10:
                            confidence = "Medium"
                        else:
                            confidence = "Low"
                        
                        patterns[feature.replace('has_', '')] = {
                            'avg_views_with': int(avg_views_with),
                            'avg_views_without': int(avg_views_without),
                            'improvement_percentage': round(improvement, 2),
                            'sample_size_with': len(with_feature),
                            'sample_size_without': len(without_feature),
                            'confidence': confidence,
                            'recommendation': 'Use this pattern' if improvement > 0 else 'Avoid this pattern'
                        }
        
        return patterns
    
    def simulate_title_change(self, current_title: str, new_title: str) -> Dict:
        """Simulate the impact of changing a title."""
        # Extract features for both titles
        current_features = self._extract_single_title_features(current_title)
        new_features = self._extract_single_title_features(new_title)
        
        # Get historical pattern analysis
        patterns = self.analyze_title_patterns()
        
        # Calculate expected improvement
        improvements = []
        pattern_details = []
        
        for feature in current_features:
            if feature in new_features and feature in patterns:
                if new_features[feature] != current_features[feature]:
                    pattern_info = patterns[feature]
                    if new_features[feature]:  # Added a positive pattern
                        improvements.append(pattern_info['improvement_percentage'])
                        pattern_details.append({
                            'pattern': feature,
                            'change': 'Added',
                            'expected_impact': pattern_info['improvement_percentage'],
                            'confidence': pattern_info.get('confidence', 'Low'),
                            'sample_size': pattern_info.get('sample_size_with', 0)
                        })
                    else:  # Removed a positive pattern
                        improvements.append(-pattern_info['improvement_percentage'])
                        pattern_details.append({
                            'pattern': feature,
                            'change': 'Removed',
                            'expected_impact': -pattern_info['improvement_percentage'],
                            'confidence': pattern_info.get('confidence', 'Low'),
                            'sample_size': pattern_info.get('sample_size_without', 0)
                        })
        
        # Calculate overall expected change with damping factor
        if improvements:
            # Apply damping to avoid unrealistic projections
            # Raw average can be too optimistic, so we use geometric mean approach
            raw_change = float(np.mean(improvements))
            # Dampen by 50% to be more conservative
            expected_change = raw_change * 0.5
            # Cap at ±25%
            expected_change = max(-25, min(25, expected_change))
        else:
            expected_change = 0.0
        
        # Calculate confidence based on number of patterns and their reliability
        confidence = self._calculate_confidence(improvements, pattern_details)
        
        # Keep both detailed and generic keys so UI can consume either
        return {
            'current_title': current_title,
            'new_title': new_title,
            'expected_ctr_change': round(expected_change, 2),
            'expected_views_change': f"{'+' if expected_change > 0 else ''}{round(expected_change, 2)}%",
            'expected_improvement': round(expected_change, 2),
            'confidence': confidence,
            'pattern_details': pattern_details,
            'sample_info': self._get_sample_info(),
            'recommendation': self._get_title_recommendation(expected_change)
        }
    
    def _get_sample_info(self) -> Dict:
        """Get information about sample size for context."""
        total_videos = len(self.df)
        return {
            'total_videos': total_videos,
            'message': f"Based on {total_videos} videos in your channel history"
        }
    
    def _extract_single_title_features(self, title: str) -> Dict:
        """Extract features from a single title."""
        title = title.lower()
        
        return {
            'number': bool(re.search(r'\d+', title)),
            'howto': 'how to' in title or 'how-to' in title,
            'tips': 'tip' in title or 'tips' in title,
            'secrets': 'secret' in title or 'secrets' in title,
            'guide': 'guide' in title or 'tutorial' in title,
            'versus': 'vs' in title or 'versus' in title,
            'list': 'list' in title,
            'review': 'review' in title,
            'myth': 'myth' in title or 'false' in title,
            'why': 'why' in title,
            'best': 'best' in title,
            'beginner': 'beginner' in title or 'start' in title,
            'advanced': 'advanced' in title or 'pro' in title,
            'question': '?' in title
        }
    
    def _calculate_confidence(self, improvements: List[float], pattern_details: List[Dict] = None) -> str:
        """Calculate confidence level based on sample size and variance."""
        if not improvements:
            return "Low"
        
        # Check sample sizes in pattern details
        if pattern_details:
            min_sample = min(p.get('sample_size', 0) for p in pattern_details)
            if min_sample < 3:
                return "Low - Need more data"
        
        # More patterns = more confidence
        if len(improvements) >= 3:
            return "Medium"
        elif len(improvements) >= 2:
            return "Low-Medium"
        else:
            return "Low - Limited data"
    
    def _get_title_recommendation(self, expected_change: float) -> str:
        """Get recommendation based on expected change."""
        if expected_change > 10:
            return "Moderately recommended - slight improvement possible"
        elif expected_change > 3:
            return "Slight improvement possible - worth testing"
        elif expected_change > -3:
            return "Minimal impact expected - title change unlikely to help"
        elif expected_change > -10:
            return "Not recommended - slight decrease possible"
        else:
            return "Avoid this change - negative impact likely"
    
    def get_best_title_keywords(self, n: int = 10) -> List[Dict]:
        """Get the best performing keywords from titles."""
        if self.df.empty:
            return []
        
        # Analyze keywords
        keyword_stats = defaultdict(lambda: {'views': [], 'count': 0})
        
        for _, row in self.df.iterrows():
            title = str(row.get('title', '')).lower()
            words = re.findall(r'\b\w+\b', title)
            
            for word in words:
                if len(word) > 3:  # Only meaningful words
                    keyword_stats[word]['views'].append(row.get('views', 0))
                    keyword_stats[word]['count'] += 1
        
        # Calculate average views per keyword
        keyword_performance = []
        for keyword, stats in keyword_stats.items():
            if stats['count'] >= 3:  # Minimum sample size
                keyword_performance.append({
                    'keyword': keyword,
                    'avg_views': int(np.mean(stats['views'])),
                    'total_videos': stats['count']
                })
        
        # Sort by average views
        keyword_performance.sort(key=lambda x: x['avg_views'], reverse=True)
        
        return keyword_performance[:n]
    
    def get_title_length_analysis(self) -> Dict:
        """Analyze optimal title length."""
        features_df = self.extract_title_features()
        
        if features_df.empty:
            return {'error': 'No data available'}
        
        # Define length buckets
        features_df['length_bucket'] = pd.cut(
            features_df['title_length'],
            bins=[0, 40, 60, 80, 100, 200],
            labels=['Very Short', 'Short', 'Medium', 'Long', 'Very Long']
        )
        
        by_length = features_df.groupby('length_bucket').agg({
            'views': 'mean',
            'ctr': 'mean',
            'video_id': 'count'
        }).rename(columns={'video_id': 'count'})
        
        best_length = by_length['views'].idxmax()
        
        return {
            'analysis': by_length.to_dict(),
            'optimal_length': best_length,
            'recommendation': f"Titles around {best_length} perform best"
        }
    
    def analyze_thumbnail(self, image_data: bytes) -> Dict:
        """Analyze thumbnail image and extract features."""
        if not PIL_AVAILABLE:
            return {
                'error': 'Image analysis not available. Install Pillow: pip install Pillow',
                'brightness': 0,
                'contrast': 0,
                'colorfulness': 0,
                'has_text_like_features': False,
                'face_like_features': False,
                'composition_score': 0
            }
        
        try:
            img = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get image stats
            stat = ImageStat.Stat(img)
            
            # Calculate brightness (0-255)
            brightness = sum(stat.mean) / 3
            
            # Calculate contrast
            r_std, g_std, b_std = stat.stddev
            contrast = (r_std + g_std + b_std) / 3
            
            # Calculate colorfulness
            r_mean, g_mean, b_mean = stat.mean
            colorfulness = abs(r_mean - g_mean) + abs(g_mean - b_mean) + abs(b_mean - r_mean)
            
            # Detect edges (indicator of text/sharp features)
            edges = img.filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)
            edge_intensity = sum(edge_stat.mean) / 3
            
            # Simple face detection proxy: look for skin-tone colored regions
            # This is a simplified heuristic
            pixels = list(img.getdata())
            skin_tone_pixels = 0
            for r, g, b in pixels:
                # Simple skin tone detection
                if (r > 60 and g > 40 and b > 20 and 
                    r > g and r > b and 
                    abs(r - g) > 15 and abs(r - b) > 15):
                    skin_tone_pixels += 1
            
            skin_ratio = skin_tone_pixels / len(pixels) if pixels else 0
            has_face_like = skin_ratio > 0.05 and skin_ratio < 0.6
            
            # Text-like features (high edge density in certain regions)
            has_text_like = edge_intensity > 20
            
            # Composition score based on brightness distribution
            brightness_variance = stat.var[0] + stat.var[1] + stat.var[2]
            composition_score = min(100, brightness_variance / 1000)
            
            return {
                'brightness': round(brightness, 2),
                'contrast': round(contrast, 2),
                'colorfulness': round(colorfulness, 2),
                'edge_intensity': round(edge_intensity, 2),
                'has_face_like_features': has_face_like,
                'has_text_like_features': has_text_like,
                'composition_score': round(composition_score, 2),
                'size': img.size,
                'aspect_ratio': round(img.size[0] / img.size[1], 2) if img.size[1] > 0 else 0
            }
            
        except Exception as e:
            return {
                'error': f'Failed to analyze image: {str(e)}',
                'brightness': 0,
                'contrast': 0,
                'colorfulness': 0,
                'has_text_like_features': False,
                'face_like_features': False,
                'composition_score': 0
            }
    
    def compare_thumbnails(self, thumb_a_data: bytes, thumb_b_data: bytes) -> Dict:
        """Compare two thumbnails and provide recommendations."""
        analysis_a = self.analyze_thumbnail(thumb_a_data)
        analysis_b = self.analyze_thumbnail(thumb_b_data)
        
        if 'error' in analysis_a or 'error' in analysis_b:
            return {
                'error': analysis_a.get('error', analysis_b.get('error', 'Analysis failed')),
                'recommendation': 'Unable to analyze thumbnails',
                'winner': None
            }
        
        # Scoring based on YouTube best practices
        score_a = 0
        score_b = 0
        reasons_a = []
        reasons_b = []
        
        # Brightness (optimal range: 100-180)
        for score, analysis, reasons in [(score_a, analysis_a, reasons_a), (score_b, analysis_b, reasons_b)]:
            brightness = analysis['brightness']
            if 100 <= brightness <= 180:
                score += 15
                reasons.append("Good brightness")
            elif brightness > 180:
                score += 5
                reasons.append("Slightly bright")
            else:
                score += 5
                reasons.append("Could be brighter")
        
        # Contrast (higher is generally better for thumbnails)
        if analysis_a['contrast'] > analysis_b['contrast']:
            score_a += 10
            reasons_a.append("Better contrast")
        elif analysis_b['contrast'] > analysis_a['contrast']:
            score_b += 10
            reasons_b.append("Better contrast")
        else:
            score_a += 5
            score_b += 5
        
        # Colorfulness (vibrant thumbnails perform better)
        if analysis_a['colorfulness'] > analysis_b['colorfulness']:
            score_a += 10
            reasons_a.append("More vibrant colors")
        elif analysis_b['colorfulness'] > analysis_a['colorfulness']:
            score_b += 10
            reasons_b.append("More vibrant colors")
        else:
            score_a += 5
            score_b += 5
        
        # Face detection (faces significantly improve CTR)
        if analysis_a['has_face_like_features']:
            score_a += 20
            reasons_a.append("Contains face (great for CTR!)")
        if analysis_b['has_face_like_features']:
            score_b += 20
            reasons_b.append("Contains face (great for CTR!)")
        
        # Text-like features (text overlays help)
        if analysis_a['has_text_like_features']:
            score_a += 15
            reasons_a.append("Has text/sharp elements")
        if analysis_b['has_text_like_features']:
            score_b += 15
            reasons_b.append("Has text/sharp elements")
        
        # Edge intensity (sharpness/clarity)
        if analysis_a['edge_intensity'] > analysis_b['edge_intensity']:
            score_a += 10
            reasons_a.append("Sharper image")
        elif analysis_b['edge_intensity'] > analysis_a['edge_intensity']:
            score_b += 10
            reasons_b.append("Sharper image")
        
        # Aspect ratio (16:9 is optimal for YouTube)
        target_ratio = 16/9  # 1.778
        diff_a = abs(analysis_a['aspect_ratio'] - target_ratio)
        diff_b = abs(analysis_b['aspect_ratio'] - target_ratio)
        
        if diff_a < diff_b:
            score_a += 10
            reasons_a.append("Better aspect ratio (closer to 16:9)")
        elif diff_b < diff_a:
            score_b += 10
            reasons_b.append("Better aspect ratio (closer to 16:9)")
        
        # Determine winner
        if score_a > score_b:
            winner = 'A'
            recommendation = f"Thumbnail A scores {score_a} vs {score_b}. " + \
                           f"It wins because: {', '.join(reasons_a[:3])}."
        elif score_b > score_a:
            winner = 'B'
            recommendation = f"Thumbnail B scores {score_b} vs {score_a}. " + \
                           f"It wins because: {', '.join(reasons_b[:3])}."
        else:
            winner = 'Tie'
            recommendation = f"Both thumbnails score equally ({score_a}). Either could work well."
        
        return {
            'winner': winner,
            'score_a': score_a,
            'score_b': score_b,
            'analysis_a': analysis_a,
            'analysis_b': analysis_b,
            'reasons_a': reasons_a,
            'reasons_b': reasons_b,
            'recommendation': recommendation,
            'improvement_tips': self._get_thumbnail_improvement_tips(analysis_a, analysis_b)
        }
    
    def _get_thumbnail_improvement_tips(self, analysis_a: Dict, analysis_b: Dict) -> List[str]:
        """Generate improvement tips based on thumbnail analysis."""
        tips = []
        
        # Check brightness
        avg_brightness = (analysis_a['brightness'] + analysis_b['brightness']) / 2
        if avg_brightness < 100:
            tips.append("📷 Increase brightness - thumbnails should be well-lit and eye-catching")
        elif avg_brightness > 200:
            tips.append("📷 Reduce brightness slightly - avoid overexposed thumbnails")
        
        # Check contrast
        avg_contrast = (analysis_a['contrast'] + analysis_b['contrast']) / 2
        if avg_contrast < 30:
            tips.append("🎨 Increase contrast - make elements pop with stronger color differences")
        
        # Check faces
        has_face = analysis_a.get('has_face_like_features') or analysis_b.get('has_face_like_features')
        if not has_face:
            tips.append("👤 Consider adding a human face with emotion - faces significantly boost CTR")
        
        # Check text
        has_text = analysis_a.get('has_text_like_features') or analysis_b.get('has_text_like_features')
        if not has_text:
            tips.append("✍️ Add bold, readable text (3-4 words max) to communicate value quickly")
        
        # Check colorfulness
        avg_color = (analysis_a['colorfulness'] + analysis_b['colorfulness']) / 2
        if avg_color < 50:
            tips.append("🌈 Use more vibrant colors - colorful thumbnails stand out in search results")
        
        # Aspect ratio
        target_ratio = 16/9
        ratio_a = analysis_a.get('aspect_ratio', 0)
        ratio_b = analysis_b.get('aspect_ratio', 0)
        if abs(ratio_a - target_ratio) > 0.2 or abs(ratio_b - target_ratio) > 0.2:
            tips.append("📐 Use 16:9 aspect ratio (1280x720) - optimal for YouTube display")
        
        if not tips:
            tips.append("✅ Both thumbnails look good! Test them to see which performs better with your audience.")
        
        return tips


def run_ab_test(df: pd.DataFrame) -> ABTestSimulator:
    """Create ABTestSimulator instance."""
    return ABTestSimulator(df)


# Test A/B Testing
if __name__ == "__main__":
    # Create sample data
    sample_data = pd.DataFrame({
        'video_id': [f'video_{i}' for i in range(1, 21)],
        'title': [
            '5 Tips for Better YouTube Videos',
            'How to Grow Your Channel Fast',
            '10 Secrets Nobody Tells You',
            'Complete Guide to Video Editing',
            'iPhone vs Android - Which is Better',
            'Top 10 List of 2024',
            'Honest Review: New Camera',
            'Why YouTube Algorithm Changed',
            'Beginner Tutorial: Getting Started',
            'Advanced Tips for Pros',
            'How I Got 1 Million Subscribers',
            '7 Tips for Viral Videos',
            'Best Camera for YouTube',
            'Is This a Myth?',
            'Quick Tips for Beginners',
            'The Secret Formula',
            'Tutorial: Complete Guide',
            'Review: Is It Worth It?',
            '5 Myths About YouTube',
            'Why Your Videos Not Growing'
        ],
        'views': [5000, 8000, 12000, 6000, 9000, 15000, 4000, 7000, 10000, 5500,
                 20000, 11000, 7500, 3500, 8500, 9500, 6500, 4500, 3000, 5500],
        'ctr': [5.0, 6.5, 8.0, 5.5, 7.0, 9.0, 4.5, 6.0, 7.5, 5.0,
               10.0, 8.5, 6.5, 4.0, 7.0, 7.5, 6.0, 4.5, 3.5, 5.0],
        'engagement_rate': [6.0, 7.5, 9.0, 6.5, 8.0, 10.0, 5.0, 7.0, 8.5, 6.0,
                          11.0, 9.5, 7.5, 4.5, 8.0, 8.5, 7.0, 5.0, 4.0, 6.0]
    })
    
    ab_test = ABTestSimulator(sample_data)
    
    print("Title Pattern Analysis:")
    patterns = ab_test.analyze_title_patterns()
    for pattern, data in patterns.items():
        print(f"\n{pattern}:")
        print(f"  Improvement: {data['improvement_percentage']}%")
        print(f"  Recommendation: {data['recommendation']}")
    
    print("\n\nTitle Change Simulation:")
    result = ab_test.simulate_title_change(
        "5 Tips for Better YouTube Videos",
        "5 Secrets for Better YouTube Videos"
    )
    print(f"Expected change: {result['expected_views_change']}")
    print(f"Recommendation: {result['recommendation']}")
