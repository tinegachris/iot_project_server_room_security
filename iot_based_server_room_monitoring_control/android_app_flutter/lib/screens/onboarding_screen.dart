import 'package:flutter/material.dart';

class OnboardingScreen extends StatefulWidget {
  @override
  _OnboardingScreenState createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<OnboardingPage> _pages = [
    OnboardingPage(
      title: 'Welcome to Server Room Security',
      description: 'Monitor and control your server room security system from anywhere.',
      icon: Icons.security,
    ),
    OnboardingPage(
      title: 'Real-time Monitoring',
      description: 'Get instant updates about your server room status, including temperature, humidity, and security alerts.',
      icon: Icons.monitor,
    ),
    OnboardingPage(
      title: 'Smart Controls',
      description: 'Control door access, view camera feeds, and manage security settings with just a few taps.',
      icon: Icons.control_point,
    ),
    OnboardingPage(
      title: 'Detailed Logs',
      description: 'Access comprehensive logs of all security events and system activities.',
      icon: Icons.history,
    ),
  ];

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _nextPage() {
    if (_currentPage < _pages.length - 1) {
      _pageController.nextPage(
        duration: Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (index) {
                  setState(() {
                    _currentPage = index;
                  });
                },
                itemCount: _pages.length,
                itemBuilder: (context, index) {
                  return _buildPage(_pages[index]);
                },
              ),
            ),
            Padding(
              padding: EdgeInsets.all(24),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(
                      _pages.length,
                      (index) => _buildDot(index),
                    ),
                  ),
                  SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: _nextPage,
                    child: Text(
                      _currentPage == _pages.length - 1
                          ? 'Get Started'
                          : 'Next',
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      Navigator.pushReplacementNamed(context, '/login');
                    },
                    child: Text('Skip'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPage(OnboardingPage page) {
    return Padding(
      padding: EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            page.icon,
            size: 120,
            color: Theme.of(context).primaryColor,
          ),
          SizedBox(height: 32),
          Text(
            page.title,
            style: Theme.of(context).textTheme.headlineMedium,
            textAlign: TextAlign.center,
          ),
          SizedBox(height: 16),
          Text(
            page.description,
            style: Theme.of(context).textTheme.bodyLarge,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildDot(int index) {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 4),
      width: 8,
      height: 8,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: _currentPage == index
            ? Theme.of(context).primaryColor
            : Colors.grey[300],
      ),
    );
  }
}

class OnboardingPage {
  final String title;
  final String description;
  final IconData icon;

  OnboardingPage({
    required this.title,
    required this.description,
    required this.icon,
  });
} 