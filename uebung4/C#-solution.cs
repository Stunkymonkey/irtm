using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using FileHelpers;

namespace NaiveBayes
{
    public class Program
    {
        // Logarithmic values are stored
        private static readonly Dictionary<string, double> GoodReviewConditionalProbabilities = new Dictionary<string, double>();
        private static readonly Dictionary<string, double> BadReviewConditionalProbabilities = new Dictionary<string, double>();

        private static List<string> _dictionary = new List<string>();
        private static List<string> _goodReviewTokenList = new List<string>();
        private static List<string> _badReviewTokenList = new List<string>();

        private static double _goodReviewPriorLogarithmicValue;
        private static double _badReviewPriorLogarithmicValue;

        private static int _goodTestReviewCount;
        private static int _badTestReviewCount;
        private static int _truePositives;
        private static int _trueNegatives;
        private static int _falseNegatives;
        private static int _falsePositives;
        private static int _undecidedCases;	

        /// <summary>
        /// Naive Bayes classifier implementation.
        /// 
        /// Performs smoothing.
        /// All probabilities are stored directly as logartitmic values to preserve value accuracy.
        /// All training and test data is cleaned from anything non-alphabetic.
        /// 
        /// Attributes are kept static to preserve readability.
        /// 
        /// All internal dependencies are kept in this file to preserve readability.
        /// 
        /// External Dependency for CSV reading: FileHelpers 
        /// (FileHelpers.dll required in the startup location. You can find the library on Nuget)
        /// 
        /// </summary>
        public static void Main(string[] args)
        {
            Console.WriteLine("Welcome to your favourite Naive Bayes classifying Utility!");
            Console.WriteLine();

            // Both the training and test documents should be in the same directory as the .exe file.
            var trainingDocumentPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, @"games-train.csv");
            var testDocumentPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, @"games-test.csv");

            Console.WriteLine("Parsing training document...");
            var gameReviewTrainingList = new FileHelperEngine<GameReview>().ReadFile(trainingDocumentPath).ToList();

            Console.WriteLine("Parsing test document...");
            var gameReviewTestList = new FileHelperEngine<GameReview>().ReadFile(testDocumentPath).ToList();

            PerformTraining(gameReviewTrainingList);

            PerformClassification(gameReviewTestList);

            EvaluateTrainingAndTestRun();

            ListMostProbableGoodGameReviewTerms();

            Console.ReadLine();
        }

        private static void PerformTraining(List<GameReview> trainingList)
        {
            Console.WriteLine();
            Console.WriteLine("Starting training...");
            Console.WriteLine("Cleaning training data...");

            trainingList = CleanReviewTextAndTitle(trainingList);

            Console.WriteLine("Calculating logarithmic prior values...");
            _goodReviewPriorLogarithmicValue =
                Math.Log(trainingList.Count(review => review.Score == ScoreClass.Good)) - Math.Log(trainingList.Count);
            Console.WriteLine($"Logarithm of good game prior is {_goodReviewPriorLogarithmicValue}.");

            _badReviewPriorLogarithmicValue =
                Math.Log(trainingList.Count(review => review.Score == ScoreClass.Bad)) - Math.Log(trainingList.Count);
            Console.WriteLine($"Logarithm of bad game prior is {_badReviewPriorLogarithmicValue}.");

            Console.WriteLine();
            Console.WriteLine("Collecting all distinct words...");
            trainingList.ForEach(review => review.Title.Split(null).ToList().ForEach(word => _dictionary.Add(word)));
            trainingList.ForEach(review => review.Text.Split(null).ToList().ForEach(word => _dictionary.Add(word)));
            _dictionary = _dictionary.Distinct().ToList();
            Console.WriteLine($"Found {_dictionary.Count} distinct words.");

            Console.WriteLine();
            Console.WriteLine("Collecting all words occuring in 'good' reviews...");
            // Collect all words from titles
            trainingList.Where(review => review.Score == ScoreClass.Good).ToList()
                .ForEach(review => review.Title.Split(null).ToList().ForEach(word => _goodReviewTokenList.Add(word)));
            // Collect all words from text
            trainingList.Where(review => review.Score == ScoreClass.Good).ToList()
                .ForEach(review => review.Text.Split(null).ToList().ForEach(word => _goodReviewTokenList.Add(word)));
            // Remove whitespace entries
            _goodReviewTokenList = _goodReviewTokenList.Where(s => !string.IsNullOrWhiteSpace(s)).ToList();
            Console.WriteLine($"Found {_goodReviewTokenList.Count} words that occur in 'good' reviews.");

            Console.WriteLine();
            Console.WriteLine("Collecting all words occuring in 'bad' reviews...");
            // Collect all words from titles
            trainingList.Where(review => review.Score == ScoreClass.Bad).ToList()
                .ForEach(review => review.Title.Split(null).ToList().ForEach(word => _badReviewTokenList.Add(word)));
            // Collect all words from text
            trainingList.Where(review => review.Score == ScoreClass.Bad).ToList()
                .ForEach(review => review.Text.Split(null).ToList().ForEach(word => _badReviewTokenList.Add(word)));
            // Remove whitespace entries
            _badReviewTokenList = _badReviewTokenList.Where(s => !string.IsNullOrWhiteSpace(s)).ToList();
            Console.WriteLine($"Found {_badReviewTokenList.Count} words that occur in 'bad' reviews.");

            Console.WriteLine();
            Console.WriteLine("Computing the conditional probabilities of every word in 'good' reviews...");
            Console.WriteLine("(This might take a lot of time, time complexity is approximately 2n)");
            _goodReviewTokenList.Distinct().ToList().ForEach(
                token => GoodReviewConditionalProbabilities.Add(token, ComputeConditionalProbabilityLogarithmicalValue(token, _goodReviewTokenList)));
            Console.WriteLine("Computing the conditional probabilities of every word in 'bad' reviews...");
            Console.WriteLine("(This might take a lot of time, time complexity is approximately 2n)");
            _badReviewTokenList.Distinct().ToList().ForEach(
                token => BadReviewConditionalProbabilities.Add(token, ComputeConditionalProbabilityLogarithmicalValue(token, _badReviewTokenList)));
        }

        private static void PerformClassification(List<GameReview> reviewList)
        {
            Console.WriteLine();
            Console.WriteLine("Starting test data classification...");
            Console.WriteLine("Cleaning test data...");

            reviewList = CleanReviewTextAndTitle(reviewList);

            _goodTestReviewCount = reviewList.Count(review => review.Score == ScoreClass.Good);
            _badTestReviewCount = reviewList.Count(review => review.Score == ScoreClass.Bad);

            foreach (var review in reviewList)
            {
                var reviewTokens = new List<string>();
                // Collect all words from the title
                review.Title.Split(null).ToList().ForEach(word => reviewTokens.Add(word));
                // Collect all words from the text
                review.Text.Split(null).ToList().ForEach(word => reviewTokens.Add(word));
                // Remove empty entries
                reviewTokens = reviewTokens.Where(s => !string.IsNullOrWhiteSpace(s)).ToList();

                var probabilityOfGoodReview = _goodReviewPriorLogarithmicValue;
                foreach (var reviewToken in reviewTokens)
                {
                    if(GoodReviewConditionalProbabilities.ContainsKey(reviewToken))
                        probabilityOfGoodReview += GoodReviewConditionalProbabilities[reviewToken];
                };

                var probabilityOfBadReview = _badReviewPriorLogarithmicValue;
                foreach (var reviewToken in reviewTokens)
                {
                    if (BadReviewConditionalProbabilities.ContainsKey(reviewToken))
                        probabilityOfBadReview += BadReviewConditionalProbabilities[reviewToken];
                }

                if (probabilityOfGoodReview > probabilityOfBadReview)
                {
                    Console.WriteLine($"This review is predicted to be 'good'. Actual review score: {review.Score}.");

                    if (review.Score == ScoreClass.Good)
                        _truePositives++;

                    if (review.Score == ScoreClass.Bad)
                        _falsePositives++;

                    continue;
                }

                if (probabilityOfGoodReview < probabilityOfBadReview)
                {
                    Console.WriteLine($"This review is predicted to be 'bad'. Actual review score: {review.Score}.");

                    if (review.Score == ScoreClass.Good)
                        _falseNegatives++;

                    if (review.Score == ScoreClass.Bad)
                        _trueNegatives++;

                    continue;
                }

                // This code normally shouldn't be reached
                Console.WriteLine($"The score of this review can't be predicted. Actual review score: {review.Score}.");
                _undecidedCases++;
            }
        }

        private static void EvaluateTrainingAndTestRun()
        {
            ////////////////////////////////////////////////////////////////////////////////////
            // Subtask 2
            ////////////////////////////////////////////////////////////////////////////////////

            double precision = (double)_truePositives / (_truePositives + _falsePositives);
            double recall = (double)_truePositives / (_truePositives + _falseNegatives);
            double fScore = 2 * precision * recall / (precision + recall);

            Console.WriteLine();
            Console.WriteLine("Starting evaluation...");
            Console.WriteLine($"TP value: {_truePositives} (out of {_goodTestReviewCount}).");
            Console.WriteLine($"TN value: {_trueNegatives} (out of {_badTestReviewCount}).");
            Console.WriteLine($"FP value: {_falsePositives}.");
            Console.WriteLine($"FN value: {_falseNegatives}.");
            Console.WriteLine($"Amount of undecided cases: {_undecidedCases} (This value should be 0).");
            Console.WriteLine($"Precision value: {precision}.");
            Console.WriteLine($"Recall value: {recall}.");
            Console.WriteLine($"F score value: {fScore}.");
        }

        private static void ListMostProbableGoodGameReviewTerms()
        {
            ////////////////////////////////////////////////////////////////////////////////////
            // Which terms have the highest probability to occur in a good review?
            ////////////////////////////////////////////////////////////////////////////////////
            
            var resultLines = GoodReviewConditionalProbabilities.OrderByDescending(
                entry => entry.Value).Select(kvp => kvp.Key + " : " + kvp.Value.ToString(CultureInfo.InvariantCulture));

            resultLines = resultLines.Take(20);
            Console.WriteLine();
            Console.WriteLine("Top 20 Most probable terms for a 'good' review:");
            Console.WriteLine("Term : conditional probability for appearing in a good review.");
            Console.WriteLine(string.Join(Environment.NewLine, resultLines));
        }

        private static List<GameReview> CleanReviewTextAndTitle(List<GameReview> reviewList)
        {
            Console.WriteLine();
            Console.WriteLine("Removing everything non-alphabetic from the review titles...");
            reviewList = reviewList.Select(
                review =>
                {
                    review.Title = CleanText(review.Title);
                    return review;
                }).ToList();

            Console.WriteLine("Removing everything non-alphabetic from the review texts...");
            reviewList = reviewList.Select(
                review =>
                {
                    review.Text = CleanText(review.Text);
                    return review;
                }).ToList();

            Console.WriteLine();
            return reviewList;
        }

        private static string CleanText(string reviewReviewTitle)
        {
            return new string(reviewReviewTitle.Where(c => char.IsLetter(c) || char.IsWhiteSpace(c)).ToArray());
        }

        private static double ComputeConditionalProbabilityLogarithmicalValue(string token, List<string> tokenList)
        {
            // Conditional Probability of a token in a class (tokenList)
            // = (token frequency in tokenList + 1) / (tokenList.Count + _trainTokenList.Count)
            // Smoothing is performed by '+1'
            return Math.Log(tokenList.Count(listToken => listToken.Equals(token)) + 1) -
                   Math.Log(_goodReviewTokenList.Count + _dictionary.Count);
        }
    }

    public enum ScoreClass
    {
        Good = 1,
        Bad = 0,
        Unknown = -1
    }

    [DelimitedRecord("\t")]
    public class GameReview
    {
        public string GameTitle { get; set; }

        [FieldConverter(typeof(ReviewScoreConverter))]
        public ScoreClass Score { get; set; }

        public string Title { get; set; }

        public string Text { get; set; }
    }

    public class ReviewScoreConverter : ConverterBase
    {
        public override object StringToField(string from)
        {
            switch (from)
            {
                case "gut": return ScoreClass.Good;
                case "schlecht": return ScoreClass.Bad;
                default: return ScoreClass.Unknown;
            }
        }

        public override string FieldToString(object fieldValue)
        {
            throw new NotImplementedException();
        }
    }
}
