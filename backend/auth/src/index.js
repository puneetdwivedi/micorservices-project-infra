import express from 'express';
import cors from 'cors';

const app = express();
const PORT = process.env.AUTHAPP_PORT || (() => {
    throw new Error("AUTHAPP_PORT is not defined");
})();;


app.use(cors());
app.use(express.json());

app.get('/api/auth', (req, res) => {
    res.json({ message: 'Authentication service is running!' });
});

app.get('/api/auth/users/:userId', (req, res)=>{
    const userId = req.params.userId;
    const users =  [
        { id: '1', name: 'Alice' },
        { id: '2', name: 'Bob' },
        { id: '3', name: 'Charlie' }
    ];
    const user = users.find(u => u.id === userId);
    if (user) {
        res.json(user);
    } else {
        res.status(404).json({ error: 'User not found' });
    }
    
})



app.listen(PORT, () => {
    console.log(`Auth service is running on port ${PORT}`);
});
