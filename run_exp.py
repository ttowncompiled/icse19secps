import random

def run_trial(alpha, beta, n, uavs, victims, adj, turns, allow_collisions):
    """
        Executes a single trial of the experiment with the provided parameters.

        INPUT:
            alpha - The probability that the UAV's sensors detect a single victim in the same zone,
            beta - The probability that a victim remains in their current zone for the next turn,
            n - The number of zones in the city,
            uavs - A dictionary of ids to integers representing the zones of the
                UAVs initial deployment configuration,
            victims - A dictionary of ids to integers representing the zones of the
                victims initial deployment configuration,
            adj - A dictionary which takes a zone i and returns the zones adjacent to i,
            turns - The number of turns to run the trial, and
            allow_collisions - Whether or not collisions are permitted.
        OUTPUT:
            A list of the mission-effectiveness of the UAVs after each system player turn.
    """
    heatmap, results = [ 1.0 / float(n) for _ in range(n) ], []
    for t in range(turns):
        # system player turn
        sys_turn, occupied_zones = {}, set({})
        for u_id, u_zone in uavs.items():
            next_zone = u_zone
            # update location of UAV
            for a_j in adj[u_zone]:
                if heatmap[a_j] > heatmap[next_zone]:
                    if a_j in occupied_zones and not allow_collisions:
                        continue
                    next_zone = a_j
            sys_turn[u_id] = next_zone
            occupied_zones = occupied_zones.union(set({ next_zone }))
            # update heatmap after performing a scan
            heatmap[next_zone] = heatmap[next_zone] * (1 - alpha)
        uavs = sys_turn
        # update mission-effectiveness
        results.append(1 - sum(heatmap))
        # environmental player turn
        env_turn = {}
        for v_id, v_zone in victims.items():
            thwart = True
            for u_id, u_zone in uavs.items():
                if u_zone == v_zone:
                    # attempt to thwart scan
                    if random.uniform(0, 1) <= alpha:
                        thwart = False
            if not thwart:
                continue
            next_zone = v_zone
            # attempt to move the victim
            if random.uniform(0, 1) > beta:
                next_zone = random.choice(adj[v_zone])
            env_turn[v_id] = next_zone
        victims = env_turn
        # update the heatmap to account for the potential moves
        for i in range(n):
            heatmap[i] = heatmap[i] * beta
            for j in adj[i]:
                heatmap[i] += heatmap[j] * (1 - beta) * 1.0 / len(adj[j])
    return results

def run_trials(uavs, victims, n, rows, cols, turns, adj, alphas, betas, trials, allow_collisions):
    for alpha in alphas:
        for beta in betas:
            final_results = [ 0.0 for t in range(turns) ]
            for trial in range(trials):
                uav_conf, occupied_zones = {}, set({})
                for u_id in uavs:
                    zone = random.randint(0, n-1)
                    while zone in occupied_zones and not allow_collisions:
                        zone = random.randint(0, n-1)
                    uav_conf[u_id] = zone
                    occupied_zones = occupied_zones.union(set({ zone }))
                victim_conf = {}
                for v_id in victims:
                    victim_conf[v_id] = random.randint(0, n-1)
                results = run_trial(alpha, beta, n, uav_conf, victim_conf,
                        adj, turns, allow_collisions)
                for t in range(turns):
                    final_results[t] += results[t]
            for t in range(turns):
                final_results[t] = final_results[t] / trials
            print(alpha, beta, final_results[-1])

def main():
    uavs = [ x for x in range(20) ]
    victims = [ y for y in range(10) ]
    n, rows, cols = 164, 4, 41
    turns = 60
    adj = {}
    for i in range(n):
        adj_list = []
        if i // cols - 1 >= 0:
            adj_list.append( (i // cols - 1) * cols + i % cols )
        if (i + 1) % cols != 0:
            adj_list.append( i + 1 )
        if i // cols + 1 < rows:
            adj_list.append( (i // cols + 1) * cols + i % cols )
        if i % 41 != 0:
            adj_list.append( i - 1 )
        adj[i] = adj_list
    alphas = [ 0.2, 0.4, 0.6, 0.8, 1.0 ]
    betas = [ 0.2, 0.4, 0.6, 0.8, 1.0 ]
    trials = 20
    run_trials(uavs, victims, n, rows, cols, turns, adj, alphas, betas, trials, False)
    run_trials(uavs, victims, n, rows, cols, turns, adj, alphas, betas, trials, True)

if __name__ == "__main__":
    main()
