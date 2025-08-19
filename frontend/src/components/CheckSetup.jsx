import React, { useState, useEffect } from 'react';
import LoginPage from './LoginPage';
import SetupPage from './SetupPage';

function CheckSetup() {
    const [setupComplete, setSetupComplete] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkStatus = async () => {
            try {
                const response = await fetch('http://10.120.120.29:8000/api/setup/status');
                if (response.ok) {
                    const data = await response.json();
                    setSetupComplete(data.setup_complete);
                } else {
                    // Handle error case, maybe assume setup is not complete
                    setSetupComplete(false);
                }
            } catch (error) {
                // Handle fetch error, maybe assume setup is not complete
                setSetupComplete(false);
            }
            setLoading(false);
        };

        checkStatus();
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }

    return setupComplete ? <LoginPage /> : <SetupPage />;
}

export default CheckSetup;